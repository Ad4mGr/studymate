<script lang="ts">
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';
	import hljs from 'highlight.js/lib/core';
	import javascript from 'highlight.js/lib/languages/javascript';
	import python from 'highlight.js/lib/languages/python';
	import java from 'highlight.js/lib/languages/java';
	import sql from 'highlight.js/lib/languages/sql';
	import cpp from 'highlight.js/lib/languages/cpp';
	import typescript from 'highlight.js/lib/languages/typescript';
	import bash from 'highlight.js/lib/languages/bash';
	import xml from 'highlight.js/lib/languages/xml';
	import php from 'highlight.js/lib/languages/php';
	import 'highlight.js/styles/atom-one-dark.css';

	hljs.registerLanguage('javascript', javascript);
	hljs.registerLanguage('python', python);
	hljs.registerLanguage('java', java);
	hljs.registerLanguage('sql', sql);
	hljs.registerLanguage('cpp', cpp);
	hljs.registerLanguage('c', cpp);
	hljs.registerLanguage('typescript', typescript);
	hljs.registerLanguage('bash', bash);
	hljs.registerLanguage('shell', bash);
	hljs.registerLanguage('xml', xml);
	hljs.registerLanguage('html', xml);
	hljs.registerLanguage('php', php);

	interface Message {
		id: string;
		role: 'user' | 'assistant';
		content: string;
	}

	let { message, isStreaming = false }: { message: Message; isStreaming?: boolean } = $props();

	const renderer = new marked.Renderer();

	renderer.code = ({ text, lang }) => {
		let highlighted: string;
		if (lang && hljs.getLanguage(lang)) {
			highlighted = hljs.highlight(text, { language: lang }).value;
		} else {
			highlighted = hljs.highlightAuto(text).value;
		}
		return `<pre><code class="hljs language-${lang || 'text'}">${highlighted}</code></pre>`;
	};

	marked.setOptions({
		breaks: true,
		gfm: true,
		renderer
	});

	function renderContent(text: string) {
		const rawHtml = marked.parse(text, { async: false });
		return DOMPurify.sanitize(rawHtml, {
			ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'code', 'pre', 'blockquote', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'span', 'div'],
			ALLOWED_ATTR: ['class', 'href', 'target', 'rel', 'lang'],
		});
	}
</script>

<div class="flex {message.role === 'user' ? 'justify-end' : 'justify-start'}">
	{#if message.role === 'user'}
		<div class="border-l-2 border-[#22d3ee] pl-3 max-w-[70%]">
			<p class="text-sm leading-relaxed text-[#e2e8f0] whitespace-pre-wrap">{message.content}</p>
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

<style>
	:global(.prose pre) {
		background: #0d0d12 !important;
		border: 1px solid #1a1a1a !important;
		border-radius: 0 !important;
		padding: 0 !important;
		margin: 1rem 0 !important;
		overflow-x: auto;
	}

	:global(.prose pre code) {
		font-family: 'JetBrains Mono', monospace !important;
		font-size: 0.875rem !important;
		line-height: 1.7 !important;
		padding: 1rem 1.25rem !important;
		background: transparent !important;
	}

	:global(.prose code:not(pre code)) {
		background: #0d0d12 !important;
		border: 1px solid #1a1a1a !important;
		border-radius: 4px !important;
		padding: 0.125rem 0.375rem !important;
		font-size: 0.8125rem !important;
		font-family: 'JetBrains Mono', monospace !important;
		color: #22d3ee !important;
	}

	:global(.prose p) {
		margin-bottom: 0.5rem !important;
		line-height: 1.75 !important;
	}

	:global(.prose ul), :global(.prose ol) {
		padding-left: 1.5rem !important;
		margin: 0.5rem 0 !important;
	}

	:global(.prose li) {
		margin: 0.25rem 0 !important;
	}

	:global(.prose h1), :global(.prose h2), :global(.prose h3), :global(.prose h4) {
		margin-top: 1rem !important;
		margin-bottom: 0.5rem !important;
		font-weight: 600 !important;
		color: #e2e8f0 !important;
	}

	:global(.prose h1) { font-size: 1.25rem !important; }
	:global(.prose h2) { font-size: 1.125rem !important; }
	:global(.prose h3) { font-size: 1rem !important; }

	:global(.prose blockquote) {
		border-left: 3px solid #22d3ee !important;
		padding-left: 1rem !important;
		margin: 0.75rem 0 !important;
		color: #64748b !important;
	}

	:global(.prose table) {
		border-collapse: collapse !important;
		width: 100% !important;
		margin: 0.75rem 0 !important;
	}

	:global(.prose th), :global(.prose td) {
		border: 1px solid #1a1a1a !important;
		padding: 0.5rem 0.75rem !important;
		text-align: left !important;
	}

	:global(.prose th) {
		background: #0d0d12 !important;
		font-weight: 600 !important;
	}

	:global(.prose a) {
		color: #22d3ee !important;
		text-decoration: underline !important;
	}

	:global(.prose hr) {
		border-color: #1a1a1a !important;
		margin: 1rem 0 !important;
	}
</style>
