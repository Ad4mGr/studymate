<script lang="ts">
	import { goto } from '$app/navigation';

	let {
		user,
		conversations = [],
		activeId = '',
		onSelect = (_id: string) => {},
		onNew = () => {},
		onDelete = (_id: string) => {}
	}: {
		user: App.Locals['user'];
		conversations?: { id: string; title: string }[];
		activeId?: string;
		onSelect?: (id: string) => void;
		onNew?: () => void;
		onDelete?: (id: string) => void;
	} = $props();

	let historyOpen = $state(false);
	let userMenuOpen = $state(false);

	function getInitials(name: string) {
		return name
			.split(' ')
			.map((n) => n[0])
			.join('')
			.toUpperCase()
			.slice(0, 2);
	}

	async function handleSignOut() {
		const formData = new FormData();
		await fetch('/profile?/signOut', { method: 'POST', body: formData });
		goto('/login');
	}
</script>

<nav class="flex items-center justify-between border-b border-[#1a1a1a] py-3">
	<a href="/" class="flex items-center gap-2.5">
		<div class="flex h-7 w-7 items-center justify-center rounded-[4px] bg-[#22d3ee] text-[11px] font-bold text-[#0a0a0f]">
			E
		</div>
		<span class="text-sm font-medium tracking-tight text-[#e2e8f0]">studymate</span>
	</a>

	<div class="flex items-center gap-3">
		{#if user}
			<button
				onclick={() => (historyOpen = !historyOpen)}
				class="text-xs uppercase tracking-wider text-[#64748b] transition hover:text-[#22d3ee]"
			>
				History
			</button>

			<div class="relative">
				<button
					onclick={() => (userMenuOpen = !userMenuOpen)}
					class="flex h-7 w-7 items-center justify-center rounded-full bg-[#1a1a1a] text-[10px] font-medium text-[#64748b] transition hover:text-[#e2e8f0]"
				>
					{getInitials(user.name)}
				</button>

				{#if userMenuOpen}
					<div
						class="fixed inset-0 z-40"
						onclick={() => (userMenuOpen = false)}
						onkeydown={(e) => e.key === 'Escape' && (userMenuOpen = false)}
						role="button"
						tabindex="-1"
					></div>

					<div class="absolute right-0 top-full z-50 mt-2 w-48 border border-[#1f1f1f] bg-[#0f0f14] p-1.5 shadow-xl">
						<div class="border-b border-[#1a1a1a] px-3 py-2">
							<p class="text-sm font-medium text-[#e2e8f0]">{user.name}</p>
							<p class="mt-0.5 text-xs text-[#64748b] truncate">{user.email}</p>
						</div>
						<a
							href="/profile"
							onclick={() => (userMenuOpen = false)}
							class="mt-1 flex items-center gap-2 px-3 py-1.5 text-sm text-[#64748b] transition hover:text-[#e2e8f0]"
						>
							Profile
						</a>
						<button
							onclick={handleSignOut}
							class="flex w-full items-center gap-2 px-3 py-1.5 text-sm text-[#64748b] transition hover:text-[#e2e8f0]"
						>
							Sign out
						</button>
					</div>
				{/if}
			</div>
		{:else}
			<a
				href="/login"
				class="border border-[#1f1f1f] px-3 py-1 text-xs font-medium text-[#64748b] uppercase tracking-wider transition hover:border-[#22d3ee] hover:text-[#22d3ee]"
			>
				Sign in
			</a>
		{/if}
	</div>
</nav>

{#if historyOpen}
	<div
		class="fixed inset-0 z-40 bg-black/60"
		onclick={() => (historyOpen = false)}
		onkeydown={(e) => e.key === 'Escape' && (historyOpen = false)}
		role="button"
		tabindex="-1"
	></div>

	<div class="fixed bottom-0 right-0 top-0 z-50 w-80 border-l border-[#1a1a1a] bg-[#0a0a0f] shadow-xl">
		<div class="flex items-center justify-between border-b border-[#1a1a1a] px-5 py-4">
			<h2 class="text-xs font-semibold uppercase tracking-widest text-[#64748b]">History</h2>
			<div class="flex items-center gap-3">
				<button
					onclick={() => { onNew(); historyOpen = false; }}
					class="text-xs text-[#22d3ee] transition hover:text-[#67e8f9]"
				>
					+ New
				</button>
				<button
					onclick={() => (historyOpen = false)}
					class="text-xs text-[#64748b] transition hover:text-[#e2e8f0]"
				>
					Close
				</button>
			</div>
		</div>

		<div class="h-[calc(100%-57px)] overflow-y-auto px-3 py-3">
			{#if conversations.length === 0}
				<p class="px-2 text-xs text-[#475569]">No conversations yet.</p>
			{:else}
				{#each conversations as conv (conv.id)}
					<div class="group flex items-center justify-between px-3 py-2.5 transition hover:bg-[#111]">
						<button
							onclick={() => { onSelect(conv.id); historyOpen = false; }}
							class="flex-1 text-left text-xs text-[#64748b] truncate {conv.id === activeId ? 'font-medium text-[#e2e8f0]' : ''}"
						>
							{conv.title}
						</button>
						<button
							onclick={() => onDelete(conv.id)}
							class="ml-2 hidden shrink-0 text-xs text-[#475569] hover:text-[#64748b] group-hover:block"
						>
							✕
						</button>
					</div>
				{/each}
			{/if}
		</div>
	</div>
{/if}
