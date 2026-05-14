<script lang="ts">
	interface Message {
		id: string;
		role: 'user' | 'assistant';
		content: string;
	}

	let { message, isStreaming = false }: { message: Message; isStreaming?: boolean } = $props();

	function renderContent(text: string) {
		const lines = text.split('\n');
		const rendered = [];
		let inCodeBlock = false;
		let codeContent = '';
		let codeLang = '';

		for (let i = 0; i < lines.length; i++) {
			const line = lines[i];

			if (line.startsWith('```')) {
				if (inCodeBlock) {
					rendered.push(`<pre class="my-2 overflow-x-auto rounded-lg bg-dark-950 px-4 py-3 text-sm text-green-400 shadow-inner"><code>${escapeHtml(codeContent)}</code></pre>`);
					codeContent = '';
					inCodeBlock = false;
				} else {
					inCodeBlock = true;
					codeLang = line.slice(3).trim();
				}
				continue;
			}

			if (inCodeBlock) {
				codeContent += (codeContent ? '\n' : '') + line;
				continue;
			}

			if (line.trim() === '') {
				rendered.push('<br />');
				continue;
			}

			const processed = processInline(line);
			rendered.push(`<p class="mb-1 last:mb-0">${processed}</p>`);
		}

		if (inCodeBlock && codeContent) {
			rendered.push(`<pre class="my-2 overflow-x-auto rounded-lg bg-dark-950 px-4 py-3 text-sm text-green-400 shadow-inner"><code>${escapeHtml(codeContent)}</code></pre>`);
		}

		return rendered.join('\n');
	}

	function processInline(text: string) {
		text = escapeHtml(text);
		text = text.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>');
		text = text.replace(/`(.+?)`/g, '<code class="rounded bg-dark-800 px-1.5 py-0.5 text-[13px] font-mono text-red-400">$1</code>');
		return text;
	}

	function escapeHtml(str: string) {
		return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
	}
</script>

<div class="flex items-end gap-2.5 {message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}">
	{#if message.role === 'assistant'}
		<div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-esprit-600 to-esprit-800 text-[10px] font-bold text-white shadow-sm shadow-esprit-900/40">
			E
		</div>
	{/if}

	<div
		class="relative max-w-[75%] {message.role === 'user'
			? 'rounded-2xl rounded-br-sm bg-gradient-to-br from-esprit-600 to-esprit-800 px-4 py-2.5 text-white shadow-lg shadow-esprit-900/30'
			: 'rounded-2xl rounded-bl-sm border border-white/[0.06] bg-white/[0.04] px-4 py-2.5 text-dark-200 shadow-sm'}"
	>
		{#if isStreaming && message.content === ''}
			<div class="flex items-center gap-1.5 px-1 py-2">
				<span class="h-2 w-2 animate-pulse rounded-full bg-esprit-400" style="animation: pulse-dot 1.4s infinite ease-in-out both"></span>
				<span class="h-2 w-2 animate-pulse rounded-full bg-esprit-400" style="animation: pulse-dot 1.4s infinite ease-in-out both 0.16s"></span>
				<span class="h-2 w-2 animate-pulse rounded-full bg-esprit-400" style="animation: pulse-dot 1.4s infinite ease-in-out both 0.32s"></span>
			</div>
		{:else}
			<div class="prose prose-sm max-w-none prose-invert">
				{@html renderContent(message.content)}
			</div>
		{/if}
	</div>
</div>
