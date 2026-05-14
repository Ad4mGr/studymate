<script lang="ts">
	import { enhance } from '$app/forms';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import type { PageServerData } from './$types';

	let { data }: { data: PageServerData } = $props();

	if (!data.user) {
		goto('/login');
	}

	function getInitials(name: string) {
		return name
			.split(' ')
			.map((n) => n[0])
			.join('')
			.toUpperCase()
			.slice(0, 2);
	}

	const createdDate = data.user?.createdAt
		? new Date(data.user.createdAt).toLocaleDateString('en-US', {
				year: 'numeric',
				month: 'long',
				day: 'numeric'
			})
		: 'Unknown';

	const stats = [
		{ label: 'Conversations', value: data.conversationCount, icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z' },
		{ label: 'Messages', value: data.messageCount, icon: 'M12 20.25c4.97 0 9-3.694 9-8.25s-4.03-8.25-9-8.25S3 7.444 3 12c0 2.104.859 4.023 2.273 5.48.432.447.74 1.04.586 1.641a4.483 4.483 0 01-.923 1.785A5.969 5.969 0 006 21c1.282 0 2.47-.402 3.445-1.087.81.22 1.668.337 2.555.337z' },
		{ label: 'Member Since', value: createdDate, icon: 'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5' }
	];
</script>

<div class="mx-auto flex max-w-2xl flex-col gap-6 px-4 py-8">
	<div class="rounded-2xl border border-white/[0.06] bg-white/[0.03] p-8 shadow-xl shadow-black/30 backdrop-blur-xl">
		<div class="flex flex-col items-center gap-4 sm:flex-row sm:items-start sm:gap-6">
			<div class="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-esprit-600 to-esprit-800 text-2xl font-bold text-white shadow-lg shadow-esprit-900/30">
				{getInitials(data.user?.name ?? 'U')}
			</div>

			<div class="flex-1 text-center sm:text-left">
				<h1 class="text-2xl font-bold text-white">{data.user?.name}</h1>
				<p class="mt-1 text-sm text-dark-400">{data.user?.email}</p>
			</div>

			<form method="post" action="?/signOut" use:enhance class="sm:self-start">
				<button
					type="submit"
					class="flex items-center gap-2 rounded-xl border border-esprit-800 px-4 py-2 text-sm font-medium text-esprit-300 transition-all hover:bg-esprit-900/30 active:scale-[0.98]"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
					</svg>
					Sign Out
				</button>
			</form>
		</div>
	</div>

	<div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
		{#each stats as stat}
			<div class="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 shadow-sm backdrop-blur-xl">
				<div class="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-esprit-900/30">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-esprit-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d={stat.icon} />
					</svg>
				</div>
				<p class="text-lg font-bold text-white">{stat.value}</p>
				<p class="mt-0.5 text-xs text-dark-500">{stat.label}</p>
			</div>
		{/each}
	</div>

	<div class="rounded-2xl border border-white/[0.06] bg-white/[0.03] p-6 shadow-xl shadow-black/30 backdrop-blur-xl">
		<h2 class="mb-4 text-sm font-semibold uppercase tracking-widest text-dark-500">Account</h2>
		<div class="space-y-3">
			<div class="flex items-center justify-between rounded-lg bg-black/20 px-4 py-3">
				<span class="text-sm text-dark-400">User ID</span>
				<span class="text-xs font-mono text-dark-500 truncate max-w-[200px]">{data.user?.id}</span>
			</div>
			<div class="flex items-center justify-between rounded-lg bg-black/20 px-4 py-3">
				<span class="text-sm text-dark-400">Email Verified</span>
				<span class="text-sm text-dark-300">{data.user?.emailVerified ? 'Yes' : 'No'}</span>
			</div>
		</div>
	</div>
</div>
