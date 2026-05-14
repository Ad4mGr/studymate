import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';
import type { PageServerLoad } from './$types';
import { auth } from '$lib/server/auth';
import { APIError } from 'better-auth/api';

export const load: PageServerLoad = (event) => {
	if (event.locals.user) {
		return redirect(302, '/');
	}
	return {};
};

export const actions: Actions = {
	signInEmail: async (event) => {
		const formData = await event.request.formData();
		const email = formData.get('email')?.toString() ?? '';
		const password = formData.get('password')?.toString() ?? '';

		if (!email) return fail(400, { message: 'Email is required' });
		if (!password) return fail(400, { message: 'Password is required' });

		try {
			await auth.api.signInEmail({
				body: {
					email,
					password,
					callbackURL: '/'
				}
			});
		} catch (error) {
			if (error instanceof APIError) {
				return fail(400, { message: error.message || 'Sign in failed' });
			}
			return fail(500, { message: 'Unexpected error' });
		}

		return redirect(302, '/');
	}
};
