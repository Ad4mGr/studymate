<script lang="ts">
	import { env } from '$env/dynamic/public';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import FlashcardDeck from '$lib/components/FlashcardDeck.svelte';

	const apiUrl = env.PUBLIC_API_URL || 'http://localhost:8000';
	const courseId = page.params.id;

	let backendToken = $state<string>('');
	let loading = $state(true);
	let generating = $state(false);
	let error = $state('');
	let flashcards = $state<{ front: string; back: string }[]>([]);

	if (!page.data.user) goto('/login');

	async function getBackendToken() {
		const res = await fetch('/api/backend-token');
		if (res.ok) {
			const data = await res.json() as { token: string };
			backendToken = data.token;
		}
	}

	async function generateFlashcards() {
		if (!backendToken) return;
		generating = true;
		error = '';
		flashcards = [];

		const res = await fetch(`${apiUrl}/courses/${courseId}/flashcards`, {
			headers: { 'Authorization': `Bearer ${backendToken}` }
		});

		if (res.ok) {
			const data = await res.json();
			flashcards = data.flashcards;
		} else {
			const err = await res.json() as { detail?: string };
			error = err.detail || 'Failed to generate flashcards';
		}

		generating = false;
	}

	$effect(() => {
		if (page.data.user) {
			getBackendToken().then(() => {
				loading = false;
			});
		}
	});
</script>

<div class="mx-auto max-w-[680px] px-4 py-8">
	<a href="/courses" class="text-xs text-[#64748b] transition hover:text-[#22d3ee]">&larr; back to courses</a>
	<h1 class="mt-4 text-2xl font-light tracking-tight text-[#e2e8f0]">Flashcards</h1>
	<p class="mt-1 text-xs text-[#64748b]">AI-generated study cards from your course material</p>

	{#if loading}
		<p class="mt-8 text-xs text-[#475569]">Loading...</p>
	{:else if flashcards.length === 0}
		<div class="mt-12 flex flex-col items-center gap-6 text-center">
			<div class="flex h-16 w-16 items-center justify-center rounded-full border border-[#1f1f1f] bg-[#0d0d12]">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-[#22d3ee]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
				</svg>
			</div>
			<div>
				<p class="text-sm text-[#e2e8f0]">No flashcards yet</p>
				<p class="mt-1 text-xs text-[#64748b]">Generate flashcards from your course material</p>
			</div>
			<button
				onclick={generateFlashcards}
				disabled={generating}
				class="border border-[#22d3ee] px-6 py-2 text-sm text-[#22d3ee] transition hover:bg-[#22d3ee]/10 disabled:opacity-50"
			>
				{generating ? 'Generating...' : 'Generate Flashcards'}
			</button>
			{#if error}
				<p class="text-xs text-[#22d3ee]">{error}</p>
			{/if}
		</div>
	{:else}
		<div class="mt-8">
			<FlashcardDeck {cards} courseId={courseId} />
		</div>
		<div class="mt-6 flex justify-center">
			<button
				onclick={generateFlashcards}
				disabled={generating}
				class="border border-[#1f1f1f] px-4 py-2 text-xs text-[#64748b] transition hover:border-[#22d3ee] hover:text-[#22d3ee] disabled:opacity-50"
			>
				{generating ? 'Regenerating...' : 'Regenerate'}
			</button>
		</div>
	{/if}
</div>
