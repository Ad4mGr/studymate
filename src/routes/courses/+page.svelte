<script lang="ts">
	import { env } from '$env/dynamic/public';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';

	const apiUrl = env.PUBLIC_API_URL || 'http://localhost:8000';

	let backendToken = $state<string>('');

	async function getBackendToken() {
		const res = await fetch('/api/backend-token');
		if (res.ok) {
			const data = await res.json() as { token: string };
			backendToken = data.token;
		}
	}

	interface Course {
		id: string;
		name: string;
		filename: string;
		chunks: number;
	}

	let courses = $state<Course[]>([]);
	let loading = $state(true);
	let uploading = $state(false);
	let name = $state('');
	let file: File | null = $state(null);
	let error = $state('');
	let dragOver = $state(false);

	if (!page.data.user) goto('/login');

	async function loadCourses() {
		if (!backendToken) return;
		const res = await fetch(`${apiUrl}/courses`, {
			headers: { 'Authorization': `Bearer ${backendToken}` }
		});
		if (res.ok) courses = await res.json();
		loading = false;
	}

	async function upload() {
		if (!file || !name.trim() || !backendToken) return;
		uploading = true;
		error = '';

		const form = new FormData();
		form.append('file', file);
		form.append('name', name.trim());

		try {
			const res = await fetch(`${apiUrl}/courses/upload`, {
				method: 'POST',
				headers: { 'Authorization': `Bearer ${backendToken}` },
				body: form
			});
			if (!res.ok) {
				const err = await res.json() as { detail?: string };
				error = err.detail || 'Upload failed';
			} else {
				name = '';
				file = null;
				await loadCourses();
			}
		} catch {
			error = 'Make sure the backend is running on port 8000';
		} finally {
			uploading = false;
		}
	}

	async function remove(courseId: string) {
		if (!backendToken) return;
		await fetch(`${apiUrl}/courses/${courseId}`, {
			method: 'DELETE',
			headers: { 'Authorization': `Bearer ${backendToken}` }
		});
		courses = courses.filter((c) => c.id !== courseId);
	}

	$effect(() => {
		if (page.data.user) {
			getBackendToken().then(() => loadCourses());
		}
	});
</script>

<div class="mx-auto max-w-[680px] px-4 py-8">
	<div class="mb-8 flex items-center justify-between">
		<div>
			<a href="/" class="text-xs text-[#64748b] transition hover:text-[#22d3ee]">&larr; back to chat</a>
			<h1 class="mt-3 text-2xl font-light tracking-tight text-[#e2e8f0]">Course materials</h1>
			<p class="mt-1 text-xs text-[#64748b]">Upload ESPRIT course PDFs to power the AI assistant</p>
		</div>
	</div>

	<div
		class="mb-8 border border-dashed border-[#1f1f1f] bg-[#0d0d12] px-6 py-6 transition {dragOver ? 'border-[#22d3ee] bg-[#22d3ee]/5' : ''}"
		ondragover={(e) => { e.preventDefault(); dragOver = true; }}
		ondragleave={() => (dragOver = false)}
		ondrop={(e) => {
			e.preventDefault();
			dragOver = false;
			const f = e.dataTransfer?.files?.[0];
			if (f?.type === 'application/pdf') file = f;
		}}
	>
		<h2 class="mb-4 text-sm font-medium text-[#e2e8f0]">Upload a PDF</h2>
		<div class="flex flex-col gap-3 sm:flex-row">
			<input
				type="text"
				bind:value={name}
				placeholder="Course name (e.g. Java POO)"
				style="caret-color: #22d3ee"
				class="flex-1 border border-[#1f1f1f] bg-[#0a0a0f] px-3 py-2 text-sm text-[#e2e8f0] placeholder-[#475569] focus:border-[#22d3ee] focus:outline-none focus:ring-0"
			/>
			<label class="flex cursor-pointer items-center gap-2 border border-[#1f1f1f] bg-[#0a0a0f] px-3 py-2 text-sm text-[#64748b] transition hover:border-[#22d3ee] hover:text-[#22d3ee]">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
				</svg>
				{file ? file.name : 'Choose PDF'}
				<input type="file" accept=".pdf" class="hidden" onchange={(e) => { file = (e.target as HTMLInputElement).files?.[0] ?? null; }} />
			</label>
			<button
				onclick={upload}
				disabled={uploading || !file || !name.trim()}
				class="bg-[#22d3ee] px-4 py-2 text-sm font-medium text-[#0a0a0f] transition hover:bg-[#67e8f9] disabled:opacity-30"
			>
				{uploading ? 'Uploading...' : 'Upload'}
			</button>
		</div>
		{#if error}
			<p class="mt-3 text-xs text-[#22d3ee]">{error}</p>
		{/if}
	</div>

	{#if loading}
		<p class="text-xs text-[#475569]">Loading courses...</p>
	{:else if courses.length === 0}
		<p class="text-xs text-[#475569]">No course materials uploaded yet.</p>
	{:else}
		<div class="space-y-2">
			{#each courses as course}
				<div class="flex items-center justify-between border border-[#1f1f1f] bg-[#0d0d12] px-4 py-3">
					<div>
						<p class="text-sm text-[#e2e8f0]">{course.name}</p>
						<p class="text-xs text-[#64748b]">{course.filename} &middot; {course.chunks} chunks</p>
					</div>
					<button
						onclick={() => remove(course.id)}
						class="text-xs text-[#64748b] transition hover:text-[#22d3ee]"
					>
						Delete
					</button>
				</div>
			{/each}
		</div>
	{/if}
</div>
