<script lang="ts">
	interface Conversation {
		id: string;
		title: string;
		createdAt: string;
		updatedAt: string;
	}

	let {
		conversations = [],
		activeId = '',
		onSelect = (_id: string) => {},
		onNew = () => {},
		onDelete = (_id: string) => {}
	}: {
		conversations: Conversation[];
		activeId: string;
		onSelect: (id: string) => void;
		onNew: () => void;
		onDelete: (id: string) => void;
	} = $props();
</script>

<aside class="flex h-full flex-col border-r border-white/[0.06] bg-black/20 backdrop-blur-xl">
	<div class="flex items-center justify-between border-b border-white/[0.06] px-4 py-3">
		<h2 class="text-xs font-semibold uppercase tracking-widest text-dark-500">History</h2>
		<button
			onclick={onNew}
			class="flex h-7 w-7 items-center justify-center rounded-lg text-dark-500 transition hover:bg-esprit-900/30 hover:text-esprit-400"
			title="New conversation"
		>
			<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
				<path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
			</svg>
		</button>
	</div>

	<div class="flex-1 overflow-y-auto px-2 py-2">
		{#if conversations.length === 0}
			<div class="flex flex-col items-center px-4 py-12 text-center">
				<svg xmlns="http://www.w3.org/2000/svg" class="mb-3 h-8 w-8 text-dark-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
				</svg>
				<span class="text-xs text-dark-600">No conversations yet</span>
			</div>
		{:else}
			{#each conversations as conv (conv.id)}
				<div
					onclick={() => onSelect(conv.id)}
					onkeydown={(e) => e.key === 'Enter' && onSelect(conv.id)}
					role="button"
					tabindex="0"
					class="group relative mb-0.5 flex w-full cursor-pointer items-center justify-between rounded-lg px-3 py-2.5 text-left text-sm transition-all {conv.id === activeId
						? 'bg-esprit-900/30 text-esprit-200 shadow-sm shadow-esprit-900/20'
						: 'text-dark-400 hover:bg-white/[0.04] hover:text-dark-200'}"
				>
					<div class="flex min-w-0 items-center gap-2.5">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 shrink-0 {conv.id === activeId ? 'text-esprit-400' : 'text-dark-600'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
						</svg>
						<span class="truncate text-xs">{conv.title}</span>
					</div>
					<button
						onclick={(e) => {
							e.stopPropagation();
							onDelete(conv.id);
						}}
						class="ml-1 hidden shrink-0 rounded p-0.5 text-dark-600 hover:bg-white/10 hover:text-red-400 group-hover:block"
						title="Delete"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
							<path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
						</svg>
					</button>
				</div>
			{/each}
		{/if}
	</div>

	<div class="border-t border-white/[0.06] px-3 py-2">
		<div class="flex items-center gap-2 rounded-lg bg-esprit-900/20 px-3 py-2">
			<div class="flex h-5 w-5 items-center justify-center rounded-full bg-esprit-600 text-[8px] font-bold text-white">E</div>
			<span class="text-[10px] font-medium text-esprit-400">ESPRIT AI Assistant</span>
		</div>
	</div>
</aside>
