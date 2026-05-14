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

		for (let i = 0; i < lines.length; i++) {
			const line = lines[i];

			if (line.startsWith('```')) {
				if (inCodeBlock) {
					rendered.push(
						`<pre class="my-4 overflow-x-auto border border-[#1a1a1a] bg-[#0d0d12] px-4 py-3 text-sm leading-relaxed" style="font-family:'JetBrains Mono',monospace;color:#22d3ee"><code>${escapeHtml(codeContent)}</code></pre>`
					);
					codeContent = '';
					inCodeBlock = false;
				} else {
					inCodeBlock = true;
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

			rendered.push(`<p class="mb-1 last:mb-0 leading-relaxed">${processInline(line)}</p>`);
		}

		if (inCodeBlock && codeContent) {
			rendered.push(
				`<pre class="my-4 overflow-x-auto border border-[#1a1a1a] bg-[#0d0d12] px-4 py-3 text-sm leading-relaxed" style="font-family:'JetBrains Mono',monospace;color:#22d3ee"><code>${escapeHtml(codeContent)}</code></pre>`
			);
		}

		return rendered.join('\n');
	}

	function processInline(text: string) {
		text = escapeHtml(text);
		text = text.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-[#e2e8f0]">$1</strong>');
		text = text.replace(
			/`(.+?)`/g,
			'<code class="rounded-[4px] bg-[#0d0d12] px-1.5 py-0.5 text-[13px]" style="font-family:\'JetBrains Mono\',monospace;color:#22d3ee">$1</code>'
		);
		return text;
	}

	function escapeHtml(str: string) {
		return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
	}
</script>

<div class="flex {message.role === 'user' ? 'justify-end' : 'justify-start'}">
	{#if message.role === 'user'}
		<div class="border-l-2 border-[#22d3ee] pl-3 max-w-[70%]">
			<p class="text-sm leading-relaxed text-[#e2e8f0]">{message.content}</p>
		</div>
	{:else}
		<div class="w-full max-w-full">
			{#if isStreaming && message.content === ''}
				<div class="flex items-center gap-1.5 py-2">
					<span class="h-1 w-1 animate-pulse rounded-full bg-[#22d3ee]"></span>
					<span class="h-1 w-1 animate-pulse rounded-full bg-[#22d3ee]" style="animation-delay: 0.16s"></span>
					<span class="h-1 w-1 animate-pulse rounded-full bg-[#22d3ee]" style="animation-delay: 0.32s"></span>
				</div>
			{:else}
				<div class="border-t border-[#22d3ee]/30 bg-[#111] px-5 py-4">
					<div class="prose prose-sm max-w-none prose-invert">
						{@html renderContent(message.content)}
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>
