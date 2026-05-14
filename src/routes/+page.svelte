<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import NavBar from '$lib/components/NavBar.svelte';
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
					content: 'Sorry, I encountered an error. Make sure the backend server is running.',
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
	<div class="flex min-h-screen items-center justify-center">
		<div class="flex items-center gap-2">
			<span class="h-1 w-1 animate-pulse rounded-full bg-[#22d3ee]"></span>
			<span class="h-1 w-1 animate-pulse rounded-full bg-[#22d3ee]" style="animation-delay: 0.16s"></span>
			<span class="h-1 w-1 animate-pulse rounded-full bg-[#22d3ee]" style="animation-delay: 0.32s"></span>
		</div>
	</div>
{:else}
	<div class="mx-auto min-h-screen max-w-[680px] px-4 pb-36 pt-4">
		<NavBar
			user={page.data.user}
			{conversations}
			activeId={activeId}
			onSelect={selectConversation}
			onNew={newConversation}
			onDelete={deleteConversation}
		/>

		{#if !activeId}
			<div class="flex flex-col items-center justify-center px-4 pt-32 text-center">
				<h1 class="text-4xl font-light leading-tight tracking-tight text-[#e2e8f0] sm:text-5xl">
					Ready to study,
				</h1>
				<h1 class="text-4xl font-bold italic leading-tight tracking-tight text-[#22d3ee] sm:text-5xl">
					let's get into it.
				</h1>
				<div class="mt-10 flex flex-wrap justify-center gap-3">
					{#each ['Explain Java inheritance', 'Help with SQL joins', 'Solve this algorithm', 'OSI model summary'] as prompt}
						<button
							onclick={async () => {
								await newConversation();
								sendMessage(prompt);
							}}
							class="border border-[#1f1f1f] px-4 py-2 text-xs transition hover:border-[#22d3ee] hover:text-[#22d3ee]"
							style="font-family:'JetBrains Mono',monospace;color:#64748b"
						>
							{prompt}
						</button>
					{/each}
				</div>
			</div>
		{:else}
			<div class="mt-6 space-y-8">
				{#each messages as msg (msg.id)}
					<MessageBubble message={msg} isStreaming={isStreaming && msg === messages[messages.length - 1]} />
				{/each}
				<div bind:this={msgEnd}></div>
			</div>
		{/if}
	</div>

	<ChatInput disabled={isStreaming} onSend={sendMessage} />
{/if}
