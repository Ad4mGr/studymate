<script lang="ts">
	import { onMount } from 'svelte';

	let {
		disabled = false,
		onSend = (_content: string) => {}
	}: {
		disabled?: boolean;
		onSend: (content: string) => void;
	} = $props();

	let inputEl: HTMLTextAreaElement;
	let value = $state('');

	function handleSend() {
		const trimmed = value.trim();
		if (!trimmed || disabled) return;
		onSend(trimmed);
		value = '';
		resizeInput();
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	}

	function resizeInput() {
		if (inputEl) {
			inputEl.style.height = 'auto';
			inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
		}
	}

	onMount(() => {
		inputEl?.focus();
	});
</script>

<div class="fixed bottom-0 left-0 right-0 border-t border-[#22d3ee]/40 bg-[#111]">
	<div class="mx-auto max-w-[680px] px-4 py-4">
		<div class="flex items-end gap-2">
			<textarea
				bind:this={inputEl}
				bind:value
				onkeydown={handleKeydown}
				oninput={resizeInput}
				disabled={disabled}
				placeholder="ask anything about your courses..."
				rows="1"
				style="caret-color: #22d3ee; font-family: 'JetBrains Mono', monospace;"
				class="max-h-30 min-h-[44px] flex-1 resize-none border-0 bg-transparent p-0 text-sm text-[#e2e8f0] placeholder-[#475569] focus:outline-none focus:ring-0 disabled:opacity-50"
			></textarea>
			<button
				onclick={handleSend}
				disabled={disabled || !value.trim()}
				class="flex h-8 w-8 shrink-0 items-center justify-center text-[#22d3ee] transition hover:text-[#67e8f9] disabled:text-[#1f1f1f] disabled:hover:text-[#1f1f1f]"
				aria-label="Send"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
				</svg>
			</button>
		</div>
	</div>
</div>
