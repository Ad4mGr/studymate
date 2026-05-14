<script lang="ts">
	import { enhance } from '$app/forms';
	import type { ActionData } from './$types';

	let { form }: { form: ActionData } = $props();
</script>

<div class="flex min-h-screen flex-col items-center justify-center bg-[#0a0a0f] px-4">
	<div class="w-full max-w-sm">
		<div class="mb-10 text-center">
			<div class="mx-auto mb-4 flex h-10 w-10 items-center justify-center bg-[#22d3ee] text-base font-bold text-[#0a0a0f]">
				E
			</div>
			<h1 class="text-2xl font-light tracking-tight text-[#e2e8f0]">Welcome back</h1>
			<p class="mt-1 text-xs text-[#64748b]">Sign in to studymate</p>
		</div>

		<form method="post" action="?/signInEmail" use:enhance class="space-y-5">
			<div>
				<label for="email" class="block text-xs font-medium uppercase tracking-wider text-[#64748b]">Email</label>
				<input
					id="email"
					type="email"
					name="email"
					required
					style="caret-color:#22d3ee"
					class="mt-1.5 block w-full border border-[#1f1f1f] bg-[#0d0d12] px-4 py-2.5 text-sm text-[#e2e8f0] placeholder-[#475569] focus:border-[#22d3ee] focus:outline-none focus:ring-0"
					placeholder="you@esprit.tn"
				/>
			</div>
			<div>
				<label for="password" class="block text-xs font-medium uppercase tracking-wider text-[#64748b]">Password</label>
				<input
					id="password"
					type="password"
					name="password"
					required
					style="caret-color:#22d3ee"
					class="mt-1.5 block w-full border border-[#1f1f1f] bg-[#0d0d12] px-4 py-2.5 text-sm text-[#e2e8f0] placeholder-[#475569] focus:border-[#22d3ee] focus:outline-none focus:ring-0"
					placeholder="••••••••"
				/>
			</div>

			{#if form?.message}
				<div class="border border-[#1f1f1f] bg-[#111] px-4 py-2.5 text-xs text-[#22d3ee]">
					{form.message}
				</div>
			{/if}

			<button
				type="submit"
				class="w-full bg-[#22d3ee] px-4 py-2.5 text-sm font-medium text-[#0a0a0f] transition hover:bg-[#67e8f9]"
			>
				Sign In
			</button>
		</form>

		<p class="mt-6 text-center text-xs text-[#475569]">
			Don't have an account?
			<a href="/register" class="text-[#22d3ee] transition hover:text-[#67e8f9]">Create one</a>
		</p>
	</div>
</div>
