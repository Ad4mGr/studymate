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
			inputEl.style.height = Math.min(inputEl.scrollHeight, 132) + 'px';
		}
	}

	onMount(() => {
		inputEl?.focus();
	});
</script>

<div class="border-t border-white/[0.06] bg-black/30 px-4 py-3 backdrop-blur-xl">
	<div class="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-white/[0.08] bg-black/40 pl-4 pr-2 py-2 shadow-sm ring-1 ring-white/[0.02] transition-all focus-within:border-esprit-700 focus-within:ring-2 focus-within:ring-esprit-900/50">
		<textarea
			bind:this={inputEl}
			bind:value
			onkeydown={handleKeydown}
			oninput={resizeInput}
			disabled={disabled}
			placeholder="Ask anything about your ESPRIT courses..."
			rows="1"
			class="max-h-32 min-h-[24px] flex-1 resize-none border-0 bg-transparent p-0 text-sm text-dark-100 placeholder-dark-600 caret-esprit-400 focus:outline-none focus:ring-0 disabled:opacity-50"
		></textarea>
		<button
			onclick={handleSend}
			disabled={disabled || !value.trim()}
			aria-label="Send message"
			class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-esprit-600 to-esprit-800 text-white shadow-sm shadow-esprit-900/30 transition-all hover:shadow-md hover:brightness-110 active:scale-95 disabled:opacity-30 disabled:shadow-none"
		>
			<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
				<path d="M3.105 2.289a.75.75 0 00-.826.95l1.414 4.925A1.5 1.5 0 005.135 9.25h6.115a.75.75 0 010 1.5H5.135a1.5 1.5 0 00-1.442 1.086l-1.414 4.926a.75.75 0 00.826.95 28.896 28.896 0 0015.293-7.154.75.75 0 000-1.115A28.897 28.897 0 003.105 2.289z" />
			</svg>
		</button>
	</div>
	<p class="mt-1.5 text-center text-[10px] text-dark-700">
		Press <kbd class="rounded border border-white/[0.08] bg-black/40 px-1 font-mono text-[10px] text-dark-500">Enter</kbd> to send &middot; <kbd class="rounded border border-white/[0.08] bg-black/40 px-1 font-mono text-[10px] text-dark-500">Shift+Enter</kbd> for new line
	</p>
</div>
