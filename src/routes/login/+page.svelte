<script lang="ts">
	import { enhance } from '$app/forms';
	import type { ActionData } from './$types';

	let { form }: { form: ActionData } = $props();
</script>

<div class="flex min-h-screen items-center justify-center bg-gradient-to-br from-black via-esprit-950/40 to-black px-4">
	<div class="w-full max-w-md">
		<div class="mb-8 text-center">
			<div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-esprit-600 to-esprit-800 shadow-lg shadow-esprit-900/40">
				<span class="text-2xl font-extrabold text-white">E</span>
			</div>
			<h1 class="text-3xl font-bold text-white">Welcome Back</h1>
			<p class="mt-1.5 text-sm text-dark-400">Sign in to <span class="font-semibold text-esprit-400">ESPRIT</span> Studymate</p>
		</div>

		<div class="rounded-2xl border border-white/[0.06] bg-white/[0.03] p-8 shadow-xl shadow-black/50 backdrop-blur-xl">
			<form method="post" action="?/signInEmail" use:enhance class="space-y-5">
				<div>
					<label for="email" class="block text-sm font-medium text-dark-300">Email</label>
					<input
						id="email"
						type="email"
						name="email"
						required
						class="mt-1.5 block w-full rounded-xl border border-white/[0.08] bg-black/40 px-4 py-2.5 text-sm text-dark-100 shadow-sm transition-all caret-esprit-400 placeholder-dark-600 focus:border-esprit-700 focus:ring-2 focus:ring-esprit-900/40 focus:outline-none"
						placeholder="you@esprit.tn"
					/>
				</div>
				<div>
					<label for="password" class="block text-sm font-medium text-dark-300">Password</label>
					<input
						id="password"
						type="password"
						name="password"
						required
						class="mt-1.5 block w-full rounded-xl border border-white/[0.08] bg-black/40 px-4 py-2.5 text-sm text-dark-100 shadow-sm transition-all caret-esprit-400 placeholder-dark-600 focus:border-esprit-700 focus:ring-2 focus:ring-esprit-900/40 focus:outline-none"
						placeholder="••••••••"
					/>
				</div>

				{#if form?.message}
					<div class="rounded-lg bg-esprit-900/30 px-4 py-2.5 text-sm text-esprit-300">
						{form.message}
					</div>
				{/if}

				<button
					type="submit"
					class="w-full rounded-xl bg-gradient-to-r from-esprit-600 to-esprit-800 px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-esprit-900/30 transition-all hover:shadow-md hover:brightness-110 active:scale-[0.98]"
				>
					Sign In
				</button>
			</form>

			<div class="mt-6 text-center">
				<p class="text-sm text-dark-500">
					Don't have an account?
					<a href="/register" class="font-medium text-esprit-400 transition hover:text-esprit-300">Create one</a>
				</p>
			</div>
		</div>

		<p class="mt-6 text-center text-xs text-dark-700">
			ESPRIT University &middot; Tunisia
		</p>
	</div>
</div>
