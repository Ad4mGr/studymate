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
</script>

<div class="mx-auto max-w-2xl px-4 py-12">
	<div class="mb-8">
		<a href="/" class="text-xs text-[#64748b] transition hover:text-[#22d3ee]">&larr; back to chat</a>
	</div>

	<div class="mb-10 flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:gap-6">
		<div class="flex h-16 w-16 shrink-0 items-center justify-center bg-[#22d3ee] text-xl font-bold text-[#0a0a0f]">
			{getInitials(data.user?.name ?? 'U')}
		</div>
		<div>
			<h1 class="text-2xl font-light tracking-tight text-[#e2e8f0]">{data.user?.name}</h1>
			<p class="mt-0.5 text-xs text-[#64748b]">{data.user?.email}</p>
		</div>
	</div>

	<div class="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
		<div class="border border-[#1f1f1f] bg-[#0d0d12] px-5 py-4">
			<p class="text-2xl font-medium text-[#e2e8f0]">{data.conversationCount}</p>
			<p class="mt-0.5 text-xs text-[#64748b]">conversations</p>
		</div>
		<div class="border border-[#1f1f1f] bg-[#0d0d12] px-5 py-4">
			<p class="text-2xl font-medium text-[#e2e8f0]">{data.messageCount}</p>
			<p class="mt-0.5 text-xs text-[#64748b]">messages</p>
		</div>
		<div class="border border-[#1f1f1f] bg-[#0d0d12] px-5 py-4">
			<p class="text-base font-medium text-[#e2e8f0]">{createdDate}</p>
			<p class="mt-0.5 text-xs text-[#64748b]">member since</p>
		</div>
	</div>

	<div class="border border-[#1f1f1f] bg-[#0d0d12] px-6 py-5">
		<h2 class="mb-3 text-xs font-semibold uppercase tracking-widest text-[#475569]">Account</h2>
		<div class="space-y-2">
			<div class="flex items-center justify-between border border-[#1a1a1a] bg-[#0a0a0f] px-4 py-2.5">
				<span class="text-xs text-[#64748b]">User ID</span>
				<span class="max-w-[200px] truncate text-xs text-[#475569]">{data.user?.id}</span>
			</div>
			<div class="flex items-center justify-between border border-[#1a1a1a] bg-[#0a0a0f] px-4 py-2.5">
				<span class="text-xs text-[#64748b]">Email verified</span>
				<span class="text-xs text-[#64748b]">{data.user?.emailVerified ? 'Yes' : 'No'}</span>
			</div>
		</div>
	</div>

	<div class="mt-8">
		<form method="post" action="?/signOut" use:enhance>
			<button
				type="submit"
				class="border border-[#1f1f1f] bg-[#0d0d12] px-4 py-2 text-xs text-[#64748b] transition hover:border-[#22d3ee] hover:text-[#22d3ee]"
			>
				Sign out
			</button>
		</form>
	</div>
</div>
