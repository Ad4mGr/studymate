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
	register: async (event) => {
		const formData = await event.request.formData();
		const email = formData.get('email')?.toString() ?? '';
		const password = formData.get('password')?.toString() ?? '';
		const name = formData.get('name')?.toString() ?? '';

		if (!name) return fail(400, { message: 'Name is required' });
		if (!email) return fail(400, { message: 'Email is required' });
		if (!password || password.length < 6) return fail(400, { message: 'Password must be at least 6 characters' });

		try {
			await auth.api.signUpEmail({
				body: {
					email,
					password,
					name,
					callbackURL: '/'
				}
			});
		} catch (error) {
			if (error instanceof APIError) {
				return fail(400, { message: error.message || 'Registration failed' });
			}
			return fail(500, { message: 'Unexpected error' });
		}

		return redirect(302, '/');
	}
};
