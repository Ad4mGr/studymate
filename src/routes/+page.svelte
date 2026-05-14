<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import ConversationList from '$lib/components/ConversationList.svelte';
	import MessageBubble from '$lib/components/MessageBubble.svelte';
	import ChatInput from '$lib/components/ChatInput.svelte';

	interface Conversation {
		id: string;
		title: string;
		createdAt: string;
		updatedAt: string;
	}

	interface Message {
		id: string;
		role: 'user' | 'assistant';
		content: string;
		createdAt: string;
	}

	let conversations = $state<Conversation[]>([]);
	let activeId = $state<string>('');
	let messages = $state<Message[]>([]);
	let isStreaming = $state(false);
	let loading = $state(true);
	let msgEnd: HTMLDivElement | undefined = $state();
	let sidebarOpen = $state(false);

	const features = [
		{ icon: 'M14.25 9.75L16.5 12l-2.25 2.25m-4.5 0L7.5 12l2.25-2.25M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z', text: 'Code examples' },
		{ icon: 'M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25', text: 'Course Q&A' },
		{ icon: 'M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z', text: 'Exam prep' },
		{ icon: 'M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18.75h3', text: 'Study plans' }
	];

	if (!page.data.user) {
		goto('/login');
	}

	async function loadConversations() {
		const res = await fetch('/api/conversations');
		if (res.ok) {
			conversations = await res.json();
		}
	}

	async function loadMessages(id: string) {
		const res = await fetch(`/api/conversations/${id}/messages`);
		if (res.ok) {
			messages = await res.json();
		}
	}

	async function selectConversation(id: string) {
		activeId = id;
		messages = [];
		sidebarOpen = false;
		await loadMessages(id);
	}

	async function newConversation() {
		const res = await fetch('/api/conversations', { method: 'POST' });
		if (res.ok) {
			const conv: Conversation = await res.json();
			conversations = [conv, ...conversations];
			activeId = conv.id;
			messages = [];
		}
	}

	async function deleteConversation(id: string) {
		await fetch(`/api/conversations/${id}`, { method: 'DELETE' });
		conversations = conversations.filter((c) => c.id !== id);
		if (activeId === id) {
			activeId = '';
			messages = [];
		}
	}

	async function saveMessage(convId: string, role: 'user' | 'assistant', content: string) {
		const res = await fetch(`/api/conversations/${convId}/messages`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ role, content })
		});
		if (res.ok) {
			const msg: Message = await res.json();
			return msg;
		}
		return null;
	}

	async function updateConversationTitle(convId: string, title: string) {
		await fetch(`/api/conversations/${convId}`, {
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ title })
		});
		conversations = conversations.map((c) => (c.id === convId ? { ...c, title } : c));
	}

	async function sendMessage(content: string) {
		if (isStreaming) return;

		let convId = activeId;

		if (!convId) {
			const res = await fetch('/api/conversations', { method: 'POST' });
			if (!res.ok) return;
			const conv: Conversation = await res.json();
			conversations = [conv, ...conversations];
			convId = conv.id;
			activeId = conv.id;
		}

		isStreaming = true;

		const userMsg = await saveMessage(convId, 'user', content);
		if (userMsg) messages = [...messages, userMsg];

		if (messages.filter((m) => m.role === 'user').length === 1) {
			updateConversationTitle(convId, content.slice(0, 50));
		}

		const history = [...messages.map((m) => ({ role: m.role, content: m.content }))];

		try {
			const response = await fetch('http://localhost:8000/chat', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ messages: history })
			});

			if (!response.ok || !response.body) {
				throw new Error('Failed to get response');
			}

			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let aiContent = '';

			const tempId = crypto.randomUUID();
			messages = [...messages, { id: tempId, role: 'assistant', content: '', createdAt: new Date().toISOString() }];

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;
				aiContent += decoder.decode(value, { stream: true });
				messages = messages.map((m) => (m.id === tempId ? { ...m, content: aiContent } : m));
			}

			await saveMessage(convId, 'assistant', aiContent);
			messages = messages.map((m) => (m.id === tempId ? { ...m, content: aiContent } : m));
		} catch {
			const errId = crypto.randomUUID();
			messages = [
				...messages,
				{
					id: errId,
					role: 'assistant',
					content: 'Sorry, I encountered an error. Please make sure the backend server is running on http://localhost:8000.',
					createdAt: new Date().toISOString()
				}
			];
		} finally {
			isStreaming = false;
		}
	}

	$effect(() => {
		if (msgEnd) {
			msgEnd.scrollIntoView({ behavior: 'smooth' });
		}
	});

	$effect(() => {
		loadConversations().then(() => {
			loading = false;
		});
	});
</script>

{#if loading}
	<div class="flex h-full items-center justify-center">
		<div class="flex items-center gap-2">
			<div class="h-2 w-2 animate-pulse rounded-full bg-esprit-500" style="animation: pulse-dot 1.4s infinite ease-in-out both"></div>
			<div class="h-2 w-2 animate-pulse rounded-full bg-esprit-500" style="animation: pulse-dot 1.4s infinite ease-in-out both 0.16s"></div>
			<div class="h-2 w-2 animate-pulse rounded-full bg-esprit-500" style="animation: pulse-dot 1.4s infinite ease-in-out both 0.32s"></div>
		</div>
	</div>
{:else}
	<div class="flex h-full">
		<div class="hidden w-64 shrink-0 sm:block">
			<ConversationList
				{conversations}
				activeId={activeId}
				onSelect={selectConversation}
				onNew={newConversation}
				onDelete={deleteConversation}
			/>
		</div>

		<div class="flex flex-1 flex-col">
			{#if !activeId}
				<div class="flex flex-1 flex-col items-center justify-center overflow-y-auto px-4 py-8">
					<div class="mx-auto max-w-lg text-center">
						<div class="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-esprit-900/40 to-esprit-950/40 shadow-inner shadow-esprit-900/20 ring-1 ring-white/[0.04]">
							<svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-esprit-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
							</svg>
						</div>
						<h1 class="mb-2 text-2xl font-bold text-white">Welcome to Studymate</h1>
						<p class="mb-8 text-sm leading-relaxed text-dark-400">
							AI study assistant for <span class="font-semibold text-esprit-400">ESPRIT</span> students.
							Get help with programming, math, networks, databases, and more.
						</p>

						<div class="mb-8 grid grid-cols-2 gap-3">
							{#each features as item}
								<div class="flex items-center gap-2.5 rounded-xl border border-white/[0.06] bg-white/[0.03] px-4 py-3 shadow-sm">
									<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-esprit-900/30">
										<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-esprit-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d={item.icon} />
										</svg>
									</div>
									<span class="text-xs font-medium text-dark-300">{item.text}</span>
								</div>
							{/each}
						</div>

						<div class="flex flex-wrap justify-center gap-2">
							{#each ['Explain Java inheritance', 'Help with SQL joins', 'Solve this algorithm', 'OSI model summary'] as prompt}
								<button
									onclick={async () => {
										await newConversation();
										sendMessage(prompt);
									}}
									class="rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-2 text-xs font-medium text-dark-300 shadow-sm transition-all hover:border-esprit-700 hover:bg-esprit-900/20 hover:text-esprit-300 hover:shadow"
								>
									{prompt}
								</button>
							{/each}
						</div>
					</div>
				</div>
			{:else}
				<div class="flex items-center border-b border-white/[0.06] bg-black/20 px-4 py-2 sm:hidden">
					<button
						onclick={() => (sidebarOpen = !sidebarOpen)}
						aria-label="Toggle sidebar"
						class="mr-2 rounded-lg p-1.5 text-dark-500 transition hover:bg-white/5"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
						</svg>
					</button>
					<span class="truncate text-sm font-medium text-dark-200">
						{conversations.find((c) => c.id === activeId)?.title ?? 'Chat'}
					</span>
				</div>

				{#if sidebarOpen}
					<div class="absolute inset-0 z-20 sm:hidden">
						<div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick={() => (sidebarOpen = false)} onkeydown={(e) => e.key === 'Escape' && (sidebarOpen = false)} role="button" tabindex="-1"></div>
						<div class="relative h-full w-64">
							<ConversationList
								{conversations}
								activeId={activeId}
								onSelect={selectConversation}
								onNew={newConversation}
								onDelete={deleteConversation}
							/>
						</div>
					</div>
				{/if}

				<div class="flex-1 overflow-y-auto">
					<div class="mx-auto max-w-3xl px-4 py-6">
						{#if messages.length === 0}
							<div class="flex h-full items-center justify-center text-sm text-dark-600">
								<div class="text-center">
									<svg xmlns="http://www.w3.org/2000/svg" class="mx-auto mb-3 h-10 w-10 text-dark-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 20.25c4.97 0 9-3.694 9-8.25s-4.03-8.25-9-8.25S3 7.444 3 12c0 2.104.859 4.023 2.273 5.48.432.447.74 1.04.586 1.641a4.483 4.483 0 01-.923 1.785A5.969 5.969 0 006 21c1.282 0 2.47-.402 3.445-1.087.81.22 1.668.337 2.555.337z" />
									</svg>
									<p class="text-dark-600">Send a message to start studying</p>
								</div>
							</div>
						{:else}
							<div class="space-y-5">
								{#each messages as msg (msg.id)}
									<MessageBubble message={msg} isStreaming={isStreaming && msg === messages[messages.length - 1]} />
								{/each}
								<div bind:this={msgEnd}></div>
							</div>
						{/if}
					</div>
				</div>
				<ChatInput disabled={isStreaming} onSend={sendMessage} />
			{/if}
		</div>
	</div>
{/if}
