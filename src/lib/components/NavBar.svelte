<script lang="ts">
	import { goto } from '$app/navigation';

	let {
		user
	}: {
		user: App.Locals['user'];
	} = $props();

	let open = $state(false);

	function getInitials(name: string) {
		return name
			.split(' ')
			.map((n) => n[0])
			.join('')
			.toUpperCase()
			.slice(0, 2);
	}

	function toggle() {
		open = !open;
	}

	function close() {
		open = false;
	}

	async function handleSignOut() {
		const formData = new FormData();
		await fetch('/profile?/signOut', { method: 'POST', body: formData });
		goto('/login');
	}
</script>

<nav class="relative z-10 flex h-14 items-center justify-between border-b border-white/[0.06] bg-black/40 px-4 backdrop-blur-2xl">
	<a href="/" class="flex items-center gap-3">
		<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-esprit-500 to-esprit-700 shadow-lg shadow-esprit-900/40">
			<span class="text-sm font-extrabold text-white">E</span>
		</div>
		<span class="text-lg font-bold text-white">Studymate</span>
		<span class="hidden rounded-full border border-esprit-700 bg-esprit-900/40 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-esprit-300 sm:inline">
			ESPRIT
		</span>
	</a>

	<div class="flex items-center gap-2">
		{#if user}
			<div class="relative">
				<button
					onclick={toggle}
					aria-label="User menu"
					class="flex items-center gap-2 rounded-xl px-3 py-1.5 text-sm text-dark-300 transition hover:bg-white/5"
				>
					<div class="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-esprit-500 to-esprit-700 text-[11px] font-bold text-white shadow-sm">
						{getInitials(user.name)}
					</div>
					<span class="hidden max-w-[120px] truncate sm:inline">{user.name}</span>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-dark-500 transition {open ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
					</svg>
				</button>

				{#if open}
					<div
						class="fixed inset-0 z-40"
						onclick={close}
						onkeydown={(e) => e.key === 'Escape' && close()}
						role="button"
						tabindex="-1"
					></div>

					<div class="absolute right-0 top-full z-50 mt-1.5 w-56 origin-top-right animate-in rounded-xl border border-white/[0.08] bg-black/80 p-1.5 shadow-2xl shadow-black/50 backdrop-blur-2xl">
						<div class="border-b border-white/[0.06] px-3 py-2.5">
							<p class="text-sm font-medium text-white">{user.name}</p>
							<p class="mt-0.5 text-xs text-dark-500 truncate">{user.email}</p>
						</div>

						<a
							href="/profile"
							onclick={close}
							class="mt-1 flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-dark-300 transition hover:bg-white/5 hover:text-white"
						>
							<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-dark-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
							</svg>
							Profile
						</a>

						<button
							onclick={handleSignOut}
							class="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-esprit-300 transition hover:bg-esprit-900/30"
						>
							<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
							</svg>
							Sign Out
						</button>
					</div>
				{/if}
			</div>
		{:else}
			<div class="flex items-center gap-2">
				<a
					href="/register"
					class="rounded-lg border border-esprit-800 px-4 py-1.5 text-sm font-medium text-esprit-300 transition hover:bg-esprit-900/20"
				>
					Register
				</a>
				<a
					href="/login"
					class="rounded-lg bg-gradient-to-r from-esprit-600 to-esprit-700 px-4 py-1.5 text-sm font-medium text-white shadow-sm shadow-esprit-900/30 transition hover:brightness-110"
				>
					Sign In
				</a>
			</div>
		{/if}
	</div>
</nav>
