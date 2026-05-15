<script lang="ts">
	import { env } from '$env/dynamic/public';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';

	const apiUrl = env.PUBLIC_API_URL || 'http://localhost:8000';

	let backendToken = $state<string>('');

	async function getBackendToken() {
		const res = await fetch('/api/backend-token');
		if (res.ok) {
			const data = (await res.json()) as { token: string };
			backendToken = data.token;
		}
	}

	interface Course {
		id: string;
		name: string;
		filename: string;
		chunks: number;
		tags: string[];
		created_at: number;
	}

	interface PreviewData {
		id: string;
		name: string;
		filename: string;
		chunks: number;
		tags: string[];
		preview: { content: string; metadata: Record<string, unknown> }[];
	}

	let courses = $state<Course[]>([]);
	let allTags = $state<string[]>([]);
	let loading = $state(true);
	let uploading = $state(false);
	let name = $state('');
	let tags = $state('');
	let file: File | null = $state(null);
	let error = $state('');
	let dragOver = $state(false);
	let searchQuery = $state('');
	let selectedTag = $state('');
	let previewCourse = $state<PreviewData | null>(null);
	let previewLoading = $state(false);
	let exportLoading = $state<string | null>(null);
	let importModalOpen = $state(false);
	let importJson = $state('');
	let importError = $state('');
	let quizModalOpen = $state(false);
	let quizCourseId = $state('');
	let quizCourseName = $state('');
	let quizSessionId = $state('');
	let quizQuestion = $state('');
	let quizAnswer = $state('');
	let quizScore = $state(0);
	let quizTotal = $state(0);
	let quizQuestionNum = $state(0);
	let quizComplete = $state(false);
	let quizSummary = $state<{ score: number; total: number; feedback: string } | null>(null);
	let quizLoading = $state(false);
	let quizError = $state('');
	let quizEvaluation = $state('');
	let quizExplanation = $state('');

	if (!page.data.user) goto('/login');

	const filteredCourses = $derived(
		courses.filter((c) => {
			const matchesSearch =
				!searchQuery ||
				c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
				c.filename.toLowerCase().includes(searchQuery.toLowerCase());
			const matchesTag = !selectedTag || c.tags.includes(selectedTag);
			return matchesSearch && matchesTag;
		})
	);

	async function loadCourses() {
		if (!backendToken) return;
		const res = await fetch(`${apiUrl}/courses`, {
			headers: { Authorization: `Bearer ${backendToken}` }
		});
		if (res.ok) courses = await res.json();
		loading = false;
	}

	async function loadTags() {
		if (!backendToken) return;
		const res = await fetch(`${apiUrl}/courses/tags`, {
			headers: { Authorization: `Bearer ${backendToken}` }
		});
		if (res.ok) allTags = await res.json();
	}

	async function upload() {
		if (!file || !name.trim() || !backendToken) return;
		uploading = true;
		error = '';

		const form = new FormData();
		form.append('file', file);
		form.append('name', name.trim());
		form.append('tags', tags.trim());

		try {
			const res = await fetch(`${apiUrl}/courses/upload`, {
				method: 'POST',
				headers: { Authorization: `Bearer ${backendToken}` },
				body: form
			});
			if (!res.ok) {
				const err = (await res.json()) as { detail?: string };
				error = err.detail || 'Upload failed';
			} else {
				name = '';
				tags = '';
				file = null;
				await Promise.all([loadCourses(), loadTags()]);
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
			headers: { Authorization: `Bearer ${backendToken}` }
		});
		courses = courses.filter((c) => c.id !== courseId);
	}

	async function preview(courseId: string) {
		previewLoading = true;
		previewCourse = null;
		const res = await fetch(`${apiUrl}/courses/${courseId}/preview`, {
			headers: { Authorization: `Bearer ${backendToken}` }
		});
		if (res.ok) previewCourse = await res.json();
		previewLoading = false;
	}

	async function exportCourse(courseId: string) {
		exportLoading = courseId;
		const res = await fetch(`${apiUrl}/courses/${courseId}/export`, {
			headers: { Authorization: `Bearer ${backendToken}` }
		});
		if (res.ok) {
			const data = await res.json();
			const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `${data.name.replace(/\s+/g, '_')}_export.json`;
			a.click();
			URL.revokeObjectURL(url);
		}
		exportLoading = null;
	}

	async function importCourse() {
		importError = '';
		try {
			const data = JSON.parse(importJson);
			const res = await fetch(`${apiUrl}/courses/import`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${backendToken}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(data)
			});
			if (res.ok) {
				importModalOpen = false;
				importJson = '';
				await loadCourses();
			} else {
				const err = (await res.json()) as { detail?: string };
				importError = err.detail || 'Import failed';
			}
		} catch {
			importError = 'Invalid JSON';
		}
	}

	async function startQuiz(courseId: string, courseName: string) {
		quizCourseId = courseId;
		quizCourseName = courseName;
		quizModalOpen = true;
		quizLoading = true;
		quizError = '';
		quizComplete = false;
		quizSummary = null;
		quizScore = 0;
		quizTotal = 0;
		quizQuestionNum = 0;
		quizEvaluation = '';
		quizExplanation = '';
		quizAnswer = '';

		const res = await fetch(`${apiUrl}/courses/${courseId}/quiz`, {
			method: 'POST',
			headers: { Authorization: `Bearer ${backendToken}` }
		});

		if (res.ok) {
			const data = (await res.json()) as any;
			quizSessionId = data.session_id;
			quizQuestion = data.question;
			quizQuestionNum = data.question_number;
		} else {
			const err = (await res.json()) as { detail?: string };
			quizError = err.detail || 'Failed to start quiz';
		}
		quizLoading = false;
	}

	async function submitQuizAnswer() {
		if (!quizAnswer.trim() || !quizSessionId) return;
		quizLoading = true;
		quizEvaluation = '';
		quizExplanation = '';

		const res = await fetch(`${apiUrl}/courses/${quizCourseId}/quiz/${quizSessionId}/answer`, {
			method: 'POST',
			headers: {
				Authorization: `Bearer ${backendToken}`,
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ answer: quizAnswer })
		});

		if (res.ok) {
			const data = await res.json();
			quizEvaluation = data.evaluation;
			quizExplanation = data.explanation;
			quizScore = data.score;
			quizTotal = data.total;

			if (data.quiz_complete) {
				quizComplete = true;
				quizSummary = data.summary;
			} else {
				quizQuestion = data.next_question;
				quizQuestionNum = quizTotal + 1;
				quizAnswer = '';
			}
		} else {
			const err = (await res.json()) as { detail?: string };
			quizError = err.detail || 'Failed to submit answer';
		}
		quizLoading = false;
	}

	function closeQuiz() {
		quizModalOpen = false;
		quizSessionId = '';
		quizQuestion = '';
		quizAnswer = '';
		quizScore = 0;
		quizTotal = 0;
		quizQuestionNum = 0;
		quizComplete = false;
		quizSummary = null;
		quizLoading = false;
		quizError = '';
		quizEvaluation = '';
		quizExplanation = '';
	}

	$effect(() => {
		if (page.data.user) {
			getBackendToken().then(() => {
				loadCourses();
				loadTags();
			});
		}
	});
</script>

<div class="mx-auto max-w-[680px] px-4 py-8">
	<div class="mb-8 flex items-center justify-between">
		<div>
			<a href="/" class="text-xs text-[#64748b] transition hover:text-[#22d3ee]"
				>&larr; back to chat</a
			>
			<h1 class="mt-3 text-2xl font-light tracking-tight text-[#e2e8f0]">Course materials</h1>
			<p class="mt-1 text-xs text-[#64748b]">Upload ESPRIT course PDFs to power the AI assistant</p>
		</div>
		<button
			onclick={() => (importModalOpen = true)}
			class="border border-[#1f1f1f] px-3 py-1.5 text-xs text-[#64748b] transition hover:border-[#22d3ee] hover:text-[#22d3ee]"
		>
			Import
		</button>
	</div>

	<div
		class="mb-6 border border-dashed border-[#1f1f1f] bg-[#0d0d12] px-6 py-6 transition {dragOver
			? 'border-[#22d3ee] bg-[#22d3ee]/5'
			: ''}"
		ondragover={(e) => {
			e.preventDefault();
			dragOver = true;
		}}
		ondragleave={() => (dragOver = false)}
		ondrop={(e) => {
			e.preventDefault();
			dragOver = false;
			const f = e.dataTransfer?.files?.[0];
			if (f?.type === 'application/pdf') file = f;
		}}
		role="region"
		aria-label="Upload PDF drop zone"
	>
		<h2 class="mb-4 text-sm font-medium text-[#e2e8f0]">Upload a PDF</h2>
		<div class="flex flex-col gap-3 sm:flex-row">
			<input
				type="text"
				bind:value={name}
				placeholder="Course name (e.g. Java POO)"
				style="caret-color: #22d3ee"
				class="flex-1 border border-[#1f1f1f] bg-[#0a0a0f] px-3 py-2 text-sm text-[#e2e8f0] placeholder-[#475569] focus:border-[#22d3ee] focus:ring-0 focus:outline-none"
			/>
			<input
				type="text"
				bind:value={tags}
				placeholder="Tags (comma-separated)"
				style="caret-color: #22d3ee"
				class="w-full border border-[#1f1f1f] bg-[#0a0a0f] px-3 py-2 text-sm text-[#e2e8f0] placeholder-[#475569] focus:border-[#22d3ee] focus:ring-0 focus:outline-none sm:w-40"
			/>
			<label
				class="flex cursor-pointer items-center gap-2 border border-[#1f1f1f] bg-[#0a0a0f] px-3 py-2 text-sm text-[#64748b] transition hover:border-[#22d3ee] hover:text-[#22d3ee]"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-4 w-4"
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
				{file ? file.name : 'Choose PDF'}
				<input
					type="file"
					accept=".pdf"
					class="hidden"
					onchange={(e) => {
						file = (e.target as HTMLInputElement).files?.[0] ?? null;
					}}
				/>
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

	{#if allTags.length > 0}
		<div class="mb-4 flex flex-wrap gap-2">
			<button
				onclick={() => (selectedTag = '')}
				class="border px-2 py-1 text-[11px] transition {selectedTag === ''
					? 'border-[#22d3ee] bg-[#22d3ee]/10 text-[#22d3ee]'
					: 'border-[#1f1f1f] text-[#64748b] hover:border-[#22d3ee]'}"
			>
				All
			</button>
			{#each allTags as tag (tag)}
				<button
					onclick={() => (selectedTag = tag)}
					class="border px-2 py-1 text-[11px] transition {selectedTag === tag
						? 'border-[#22d3ee] bg-[#22d3ee]/10 text-[#22d3ee]'
						: 'border-[#1f1f1f] text-[#64748b] hover:border-[#22d3ee]'}"
				>
					{tag}
				</button>
			{/each}
		</div>
	{/if}

	<div class="mb-4">
		<input
			type="text"
			bind:value={searchQuery}
			placeholder="Search courses..."
			style="caret-color: #22d3ee"
			class="w-full border border-[#1f1f1f] bg-[#0a0a0f] px-3 py-2 text-sm text-[#e2e8f0] placeholder-[#475569] focus:border-[#22d3ee] focus:ring-0 focus:outline-none"
		/>
	</div>

	{#if loading}
		<p class="text-xs text-[#475569]">Loading courses...</p>
	{:else if filteredCourses.length === 0}
		<p class="text-xs text-[#475569]">
			{courses.length === 0
				? 'No course materials uploaded yet.'
				: 'No courses match your filters.'}
		</p>
	{:else}
		<div class="space-y-2">
			{#each filteredCourses as course (course.id)}
				<div
					class="flex items-center justify-between border border-[#1f1f1f] bg-[#0d0d12] px-4 py-3"
				>
					<div class="min-w-0 flex-1">
						<p class="text-sm text-[#e2e8f0]">{course.name}</p>
						<p class="text-xs text-[#64748b]">{course.filename} &middot; {course.chunks} chunks</p>
						{#if course.tags.length > 0}
							<div class="mt-1 flex flex-wrap gap-1">
								{#each course.tags as tag (tag)}
									<span
										class="rounded border border-[#1f1f1f] bg-[#0a0a0f] px-1.5 py-0.5 text-[10px] text-[#22d3ee]"
										>{tag}</span
									>
								{/each}
							</div>
						{/if}
					</div>
					<div class="flex shrink-0 items-center gap-2">
						<button
							onclick={() => preview(course.id)}
							class="text-xs text-[#64748b] transition hover:text-[#22d3ee]"
							title="Preview"
						>
							Preview
						</button>
						<a
							href="/courses/{course.id}/flashcards"
							class="text-xs text-[#64748b] transition hover:text-[#22d3ee]"
							title="Flashcards"
						>
							Flashcards
						</a>
						<button
							onclick={() => startQuiz(course.id, course.name)}
							class="text-xs text-[#64748b] transition hover:text-[#22d3ee]"
							title="Quiz"
						>
							Quiz
						</button>
						<button
							onclick={() => exportCourse(course.id)}
							class="text-xs text-[#64748b] transition hover:text-[#22d3ee]"
							title="Export"
						>
							{exportLoading === course.id ? '...' : 'Export'}
						</button>
						<button
							onclick={() => remove(course.id)}
							class="text-xs text-[#64748b] transition hover:text-[#22d3ee]"
						>
							Delete
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}

	{#if quizModalOpen}
		<div
			class="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
			onclick={closeQuiz}
		>
			<div
				class="mx-4 w-full max-w-lg border border-[#1f1f1f] bg-[#0d0d12] p-6"
				onclick={(e) => e.stopPropagation()}
			>
				<div class="mb-4 flex items-center justify-between">
					<div>
						<h3 class="text-lg font-medium text-[#e2e8f0]">Quiz: {quizCourseName}</h3>
						{#if !quizComplete}
							<p class="text-xs text-[#64748b]">
								Question {quizQuestionNum}/5 &middot; Score: {quizScore}/{quizTotal}
							</p>
						{/if}
					</div>
					<button onclick={closeQuiz} class="text-[#64748b] transition hover:text-[#22d3ee]"
						>✕</button
					>
				</div>

				{#if quizLoading && !quizQuestion}
					<p class="text-xs text-[#475569]">Starting quiz...</p>
				{:else if quizError}
					<p class="text-xs text-[#22d3ee]">{quizError}</p>
					<button
						onclick={() => startQuiz(quizCourseId, quizCourseName)}
						class="mt-3 border border-[#22d3ee] px-4 py-1.5 text-xs text-[#22d3ee] transition hover:bg-[#22d3ee]/10"
						>Retry</button
					>
				{:else if quizComplete && quizSummary}
					<div class="space-y-4">
						<div class="rounded-lg border border-[#22d3ee]/30 bg-[#22d3ee]/5 p-4 text-center">
							<p class="text-3xl font-bold text-[#22d3ee]">
								{quizSummary.score}/{quizSummary.total}
							</p>
							<p class="mt-1 text-xs text-[#64748b]">Final Score</p>
						</div>
						{#if quizSummary.feedback}
							<div class="rounded-lg border border-[#1f1f1f] bg-[#0a0a0f] p-3">
								<p class="text-xs text-[#e2e8f0]">{quizSummary.feedback}</p>
							</div>
						{/if}
						<button
							onclick={closeQuiz}
							class="w-full bg-[#22d3ee] py-2 text-sm font-medium text-[#0a0a0f] transition hover:bg-[#67e8f9]"
							>Close</button
						>
					</div>
				{:else if quizQuestion}
					<div class="space-y-4">
						{#if quizEvaluation}
							<div
								class="rounded-lg border {quizEvaluation === 'correct'
									? 'border-green-500/30 bg-green-500/5'
									: quizEvaluation === 'incorrect'
										? 'border-red-500/30 bg-red-500/5'
										: 'border-yellow-500/30 bg-yellow-500/5'} p-3"
							>
								<p
									class="text-xs font-medium {quizEvaluation === 'correct'
										? 'text-green-400'
										: quizEvaluation === 'incorrect'
											? 'text-red-400'
											: 'text-yellow-400'}"
								>
									{quizEvaluation === 'correct'
										? '✓ Correct!'
										: quizEvaluation === 'incorrect'
											? '✗ Incorrect'
											: '~ Partial'}
								</p>
								<p class="mt-1 text-xs text-[#e2e8f0]">{quizExplanation}</p>
							</div>
						{/if}

						<div class="rounded-lg border border-[#1f1f1f] bg-[#0a0a0f] p-4">
							<p class="text-sm text-[#e2e8f0]">{quizQuestion}</p>
						</div>

						{#if !quizEvaluation}
							<textarea
								bind:value={quizAnswer}
								placeholder="Type your answer..."
								style="caret-color: #22d3ee"
								class="h-24 w-full border border-[#1f1f1f] bg-[#0a0a0f] px-3 py-2 text-xs text-[#e2e8f0] placeholder-[#475569] focus:border-[#22d3ee] focus:ring-0 focus:outline-none"
							></textarea>
							<button
								onclick={submitQuizAnswer}
								disabled={quizLoading || !quizAnswer.trim()}
								class="w-full bg-[#22d3ee] py-2 text-sm font-medium text-[#0a0a0f] transition hover:bg-[#67e8f9] disabled:opacity-30"
							>
								{quizLoading ? 'Submitting...' : 'Submit Answer'}
							</button>
						{:else}
							<button
								onclick={submitQuizAnswer}
								disabled={quizLoading}
								class="w-full bg-[#22d3ee] py-2 text-sm font-medium text-[#0a0a0f] transition hover:bg-[#67e8f9] disabled:opacity-30"
							>
								{quizLoading ? 'Loading...' : 'Next Question'}
							</button>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	{/if}

	{#if previewCourse || previewLoading}
		<div
			class="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
			onclick={() => (previewCourse = null)}
		>
			<div
				class="mx-4 w-full max-w-lg border border-[#1f1f1f] bg-[#0d0d12] p-6"
				onclick={(e) => e.stopPropagation()}
			>
				<div class="mb-4 flex items-center justify-between">
					<h3 class="text-lg font-medium text-[#e2e8f0]">{previewCourse?.name || 'Loading...'}</h3>
					<button
						onclick={() => (previewCourse = null)}
						class="text-[#64748b] transition hover:text-[#22d3ee]">✕</button
					>
				</div>
				{#if previewLoading}
					<p class="text-xs text-[#475569]">Loading preview...</p>
				{:else if previewCourse}
					<p class="mb-3 text-xs text-[#64748b]">
						{previewCourse.chunks} chunks &middot; {previewCourse.filename}
					</p>
					{#if previewCourse.tags.length > 0}
						<div class="mb-3 flex flex-wrap gap-1">
							{#each previewCourse.tags as tag (tag)}
								<span
									class="rounded border border-[#1f1f1f] bg-[#0a0a0f] px-1.5 py-0.5 text-[10px] text-[#22d3ee]"
									>{tag}</span
								>
							{/each}
						</div>
					{/if}
					<div class="max-h-80 space-y-3 overflow-y-auto">
						{#each previewCourse.preview as chunk (chunk.content.slice(0, 50))}
							<div class="border border-[#1f1f1f] bg-[#0a0a0f] p-3">
								<p class="text-xs leading-relaxed whitespace-pre-wrap text-[#e2e8f0]">
									{chunk.content}...
								</p>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	{/if}

	{#if importModalOpen}
		<div
			class="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
			onclick={() => (importModalOpen = false)}
		>
			<div
				class="mx-4 w-full max-w-lg border border-[#1f1f1f] bg-[#0d0d12] p-6"
				onclick={(e) => e.stopPropagation()}
			>
				<div class="mb-4 flex items-center justify-between">
					<h3 class="text-lg font-medium text-[#e2e8f0]">Import Course</h3>
					<button
						onclick={() => (importModalOpen = false)}
						class="text-[#64748b] transition hover:text-[#22d3ee]">✕</button
					>
				</div>
				<textarea
					bind:value={importJson}
					placeholder="Paste exported course JSON here..."
					class="mb-3 h-40 w-full border border-[#1f1f1f] bg-[#0a0a0f] px-3 py-2 text-xs text-[#e2e8f0] placeholder-[#475569] focus:border-[#22d3ee] focus:ring-0 focus:outline-none"
				></textarea>
				{#if importError}
					<p class="mb-3 text-xs text-[#22d3ee]">{importError}</p>
				{/if}
				<button
					onclick={importCourse}
					disabled={!importJson.trim()}
					class="w-full bg-[#22d3ee] py-2 text-sm font-medium text-[#0a0a0f] transition hover:bg-[#67e8f9] disabled:opacity-30"
				>
					Import
				</button>
			</div>
		</div>
	{/if}
</div>
