<script lang="ts">
	import { env } from '$env/dynamic/public';
	import { page } from '$app/state';
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

	interface Course {
		id: string;
		name: string;
		filename: string;
		chunks: number;
	}

	let conversations = $state<Conversation[]>([]);
	let activeId = $state<string>('');
	let messages = $state<Message[]>([]);
	let isStreaming = $state(false);
	let loading = $state(true);
	let msgEnd: HTMLDivElement | undefined = $state();

	const apiUrl = env.PUBLIC_API_URL || 'http://localhost:8000';

	let availableCourses = $state<Course[]>([]);
	let attachedCourseIds = $state<string[]>([]);
	let coursePickerOpen = $state(false);
	let uploadName = $state('');
	let uploadFile: File | null = $state(null);
	let uploading = $state(false);
	let uploadError = $state('');

	async function loadCourses() {
		const res = await fetch(`${apiUrl}/courses`);
		if (res.ok) availableCourses = await res.json();
	}

	const attachedCourses = $derived(
		availableCourses.filter((c) => attachedCourseIds.includes(c.id))
	);

	function toggleCourse(id: string) {
		if (attachedCourseIds.includes(id)) {
			attachedCourseIds = attachedCourseIds.filter((c) => c !== id);
		} else {
			attachedCourseIds = [...attachedCourseIds, id];
		}
	}

	async function uploadCourse() {
		if (!uploadFile || !uploadName.trim()) return;
		uploading = true;
		uploadError = '';

		const form = new FormData();
		form.append('file', uploadFile);
		form.append('name', uploadName.trim());

		try {
			const res = await fetch(`${apiUrl}/courses/upload`, {
				method: 'POST',
				body: form
			});
			if (!res.ok) {
				const err = (await res.json()) as { detail?: string };
				uploadError = err.detail || 'Upload failed';
			} else {
				uploadName = '';
				uploadFile = null;
				const newCourse = (await res.json()) as Course;
			}
		} catch {
			uploadError = 'Backend not running on port 8000';
		} finally {
			uploading = false;
		}
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
			const response = await fetch(`${apiUrl}/chat`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ messages: history, course_ids: attachedCourseIds })
			});

			if (!response.ok || !response.body) {
				throw new Error('Failed to get response');
			}

			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let raw = '';

			const tempId = crypto.randomUUID();
			messages = [
				...messages,
				{ id: tempId, role: 'assistant', content: '', createdAt: new Date().toISOString() }
			];

			let sourcesLine = '';

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;
				raw += decoder.decode(value, { stream: true });

				if (!sourcesLine) {
					const nl = raw.indexOf('\n');
					if (nl !== -1) {
						sourcesLine = raw.slice(0, nl);
						raw = raw.slice(nl + 1);
					}
				}

				messages = messages.map((m) => (m.id === tempId ? { ...m, content: raw } : m));
			}

			let aiContent = raw;

			if (sourcesLine) {
				try {
					const parsed = JSON.parse(sourcesLine);
					if (parsed.sources?.length) {
						const cite = parsed.sources.map((s: { filename: string }) => s.filename).join(', ');
						aiContent += `\n\n— *Sources: ${cite}*`;
					}
				} catch {
					aiContent = raw;
				}
			}

			messages = messages.map((m) => (m.id === tempId ? { ...m, content: aiContent } : m));
			await saveMessage(convId, 'assistant', aiContent);
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
		Promise.all([loadConversations(), loadCourses()]).then(() => {
			loading = false;
		});
	});
</script>

{#if loading}
	<div class="flex min-h-screen items-center justify-center">
		<div class="flex items-center gap-2">
			<span class="h-1 w-1 animate-pulse rounded-full bg-[#22d3ee]"></span>
			<span class="h-1 w-1 animate-pulse rounded-full bg-[#22d3ee]" style="animation-delay: 0.16s"
			></span>
			<span class="h-1 w-1 animate-pulse rounded-full bg-[#22d3ee]" style="animation-delay: 0.32s"
			></span>
		</div>
	</div>
{:else}
	<div class="mx-auto min-h-screen max-w-[680px] px-4 pt-4 pb-36">
		<NavBar
			user={page.data.user}
			{conversations}
			{activeId}
			onSelect={selectConversation}
			onNew={newConversation}
			onDelete={deleteConversation}
		/>

		{#if !activeId}
			<div class="flex flex-col items-center justify-center px-4 pt-32 text-center">
				<h1 class="text-4xl leading-tight font-light tracking-tight text-[#e2e8f0] sm:text-5xl">
					Ready to study,
				</h1>
				<h1
					class="text-4xl leading-tight font-bold tracking-tight text-[#22d3ee] italic sm:text-5xl"
				>
					let's get into it.
				</h1>
				<div class="mt-10 flex flex-wrap justify-center gap-3">
					{#each ['Explain Java inheritance', 'Help with SQL joins', 'Solve this algorithm', 'OSI model summary'] as prompt (prompt)}
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
					<MessageBubble
						message={msg}
						isStreaming={isStreaming && msg === messages[messages.length - 1]}
					/>
				{/each}
				<div bind:this={msgEnd}></div>
			</div>
		{/if}
	</div>

	<div class="fixed right-0 bottom-0 left-0 z-30">
		{#if attachedCourses.length > 0}
			<div class="border-t border-[#22d3ee]/20 bg-[#0d0d12] px-4 py-2">
				<div class="mx-auto flex max-w-[680px] flex-wrap items-center gap-2">
					{#each attachedCourses as course (course.id)}
						<div class="flex items-center gap-1.5 border border-[#1f1f1f] bg-[#0a0a0f] px-2.5 py-1">
							<span class="text-[11px] text-[#22d3ee]">{course.name}</span>
							<button
								onclick={() => toggleCourse(course.id)}
								class="text-[10px] text-[#64748b] transition hover:text-[#22d3ee]"
							>
								✕
							</button>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<ChatInput disabled={isStreaming} onSend={sendMessage}>
			<div class="relative shrink-0">
				<button
					onclick={() => (coursePickerOpen = !coursePickerOpen)}
					class="flex h-8 w-8 items-center justify-center border border-[#1f1f1f] bg-[#0d0d12] text-[#64748b] transition hover:border-[#22d3ee] hover:text-[#22d3ee]"
					title="Attach courses"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-3.5 w-3.5"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 4v16m8-8H4"
						/>
					</svg>
				</button>

				{#if coursePickerOpen}
					<div
						class="fixed inset-0 z-30"
						onclick={() => (coursePickerOpen = false)}
						onkeydown={(e) => e.key === 'Escape' && (coursePickerOpen = false)}
						role="button"
						tabindex="-1"
					></div>

					<div
						class="absolute bottom-full left-0 z-40 mb-3 w-80 border border-[#1f1f1f] bg-[#0d0d12] shadow-xl"
					>
						<div class="border-b border-[#1f1f1f] px-4 py-3">
							<p class="text-xs font-medium text-[#e2e8f0]">Course materials</p>
							<p class="mt-1 text-[10px] text-[#475569]">
								Upload a PDF or select attached courses to use as AI context
							</p>
						</div>

						<div class="border-b border-[#1f1f1f] px-4 py-3">
							<p class="mb-2 text-[10px] font-medium tracking-wider text-[#475569] uppercase">
								Upload new
							</p>
							<div class="flex flex-col gap-2">
								<input
									type="text"
									bind:value={uploadName}
									placeholder="Course name (e.g. Java POO)"
									style="caret-color:#22d3ee"
									class="w-full border border-[#1f1f1f] bg-[#0a0a0f] px-2.5 py-1.5 text-xs text-[#e2e8f0] placeholder-[#475569] focus:border-[#22d3ee] focus:outline-none"
								/>
								<div class="flex gap-2">
									<label
										class="flex cursor-pointer items-center gap-1.5 border border-[#1f1f1f] bg-[#0a0a0f] px-2.5 py-1.5 text-xs text-[#64748b] transition hover:border-[#22d3ee]"
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="h-3 w-3"
											fill="none"
											viewBox="0 0 24 24"
											stroke="currentColor"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
											/>
										</svg>
										{uploadFile ? uploadFile.name : 'Choose PDF'}
										<input
											type="file"
											accept=".pdf"
											class="hidden"
											onchange={(e) => {
												uploadFile = (e.target as HTMLInputElement).files?.[0] ?? null;
											}}
										/>
									</label>
									<button
										onclick={uploadCourse}
										disabled={uploading || !uploadFile || !uploadName.trim()}
										class="bg-[#22d3ee] px-3 py-1.5 text-xs font-medium text-[#0a0a0f] transition hover:bg-[#67e8f9] disabled:opacity-30"
									>
										{uploading ? 'Uploading...' : 'Upload'}
									</button>
								</div>
								{#if uploadError}
									<p class="text-[10px] text-[#22d3ee]">{uploadError}</p>
								{/if}
							</div>
						</div>

						<div class="max-h-48 overflow-y-auto">
							{#if availableCourses.length === 0}
								<p class="px-4 py-4 text-[10px] text-[#475569]">
									No courses uploaded yet — use the form above.
								</p>
							{:else}
								{#each availableCourses as course (course.id)}
									<button
										onclick={() => toggleCourse(course.id)}
										class="flex w-full items-center gap-3 px-4 py-2.5 text-left text-xs transition hover:bg-[#1a1a1a]"
									>
										<div
											class="flex h-4 w-4 shrink-0 items-center justify-center border border-[#475569] {attachedCourseIds.includes(
												course.id
											)
												? 'border-[#22d3ee] bg-[#22d3ee]'
												: ''}"
										>
											{#if attachedCourseIds.includes(course.id)}
												<svg
													xmlns="http://www.w3.org/2000/svg"
													class="h-3 w-3 text-[#0a0a0f]"
													viewBox="0 0 20 20"
													fill="currentColor"
												>
													<path
														d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
													/>
												</svg>
											{/if}
										</div>
										<div class="min-w-0 flex-1">
											<p class="truncate text-[#e2e8f0]">{course.name}</p>
											<p class="truncate text-[#475569]">
												{course.filename} &middot; {course.chunks} chunks
											</p>
										</div>
									</button>
								{/each}
							{/if}
						</div>
					</div>
				{/if}
			</div>
		</ChatInput>
	</div>
{/if}
