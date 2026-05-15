<script lang="ts">
	import { spring } from 'svelte/motion';

	interface Flashcard {
		front: string;
		back: string;
	}

	let { cards, courseId }: { cards: Flashcard[]; courseId: string } = $props();

	let currentIndex = $state(0);
	let isFlipped = $state(false);
	let flipProgress = $state(0);

	const springConfig = { stiffness: 0.15, damping: 0.8 };
	const flipSpring = spring(0, springConfig);

	$effect(() => {
		flipProgress = $flipSpring;
	});

	function flip() {
		isFlipped = !isFlipped;
		flipSpring.set(isFlipped ? 180 : 0);
	}

	function next() {
		if (currentIndex < cards.length - 1) {
			isFlipped = false;
			flipSpring.set(0);
			currentIndex++;
		}
	}

	function prev() {
		if (currentIndex > 0) {
			isFlipped = false;
			flipSpring.set(0);
			currentIndex--;
		}
	}

	const rotateY = $derived(flipProgress);
	const progress = $derived(((currentIndex + 1) / cards.length) * 100);
</script>

<div class="flex flex-col items-center gap-6">
	<div class="flex w-full items-center justify-between text-xs text-[#64748b]">
		<span>Card {currentIndex + 1} of {cards.length}</span>
		<span class="text-[#22d3ee]">{Math.round(progress)}%</span>
	</div>

	<div class="w-full h-1 bg-[#1a1a1a] rounded-full overflow-hidden">
		<div class="h-full bg-[#22d3ee] transition-all duration-300" style="width: {progress}%"></div>
	</div>

	<div
		class="relative w-full cursor-pointer"
		style="height: 280px; perspective: 1000px;"
		onclick={flip}
		role="button"
		tabindex="0"
		onkeydown={(e) => e.key === 'Enter' && flip()}
	>
		<div
			class="absolute inset-0 transition-transform duration-500"
			style="transform-style: preserve-3d; transform: rotateY({rotateY}deg);"
		>
			<div
				class="absolute inset-0 flex flex-col items-center justify-center border border-[#1f1f1f] bg-[#0d0d12] px-8 py-6"
				style="backface-visibility: hidden;"
			>
				<span class="mb-3 text-[10px] uppercase tracking-widest text-[#22d3ee]">Question</span>
				<p class="text-center text-lg leading-relaxed text-[#e2e8f0]">{cards[currentIndex].front}</p>
				<p class="mt-4 text-xs text-[#475569]">Click to reveal answer</p>
			</div>

			<div
				class="absolute inset-0 flex flex-col items-center justify-center border border-[#22d3ee]/30 bg-[#0d0d12] px-8 py-6"
				style="backface-visibility: hidden; transform: rotateY(180deg);"
			>
				<span class="mb-3 text-[10px] uppercase tracking-widest text-[#22d3ee]">Answer</span>
				<p class="text-center text-base leading-relaxed text-[#e2e8f0]">{cards[currentIndex].back}</p>
			</div>
		</div>
	</div>

	<div class="flex items-center gap-4">
		<button
			onclick={prev}
			disabled={currentIndex === 0}
			class="border border-[#1f1f1f] px-4 py-2 text-sm text-[#64748b] transition hover:border-[#22d3ee] hover:text-[#22d3ee] disabled:opacity-30 disabled:cursor-not-allowed"
		>
			Previous
		</button>
		<button
			onclick={flip}
			class="border border-[#22d3ee]/50 px-4 py-2 text-sm text-[#22d3ee] transition hover:bg-[#22d3ee]/10"
		>
			Flip
		</button>
		<button
			onclick={next}
			disabled={currentIndex === cards.length - 1}
			class="border border-[#1f1f1f] px-4 py-2 text-sm text-[#64748b] transition hover:border-[#22d3ee] hover:text-[#22d3ee] disabled:opacity-30 disabled:cursor-not-allowed"
		>
			Next
		</button>
	</div>

	<p class="text-xs text-[#475569]">Use ← → arrow keys or click to navigate</p>
</div>
