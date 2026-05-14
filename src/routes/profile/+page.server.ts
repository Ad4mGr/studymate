import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { auth } from '$lib/server/auth';
import { db } from '$lib/server/db';
import { conversation, message } from '$lib/server/db/schema';
import { eq, count, inArray } from 'drizzle-orm';
import { APIError } from 'better-auth/api';

export const load: PageServerLoad = async (event) => {
	if (!event.locals.user) throw redirect(302, '/login');

	const userId = event.locals.user.id;

	const [convResult] = await db
		.select({ count: count() })
		.from(conversation)
		.where(eq(conversation.userId, userId));

	const convRows = await db
		.select({ id: conversation.id })
		.from(conversation)
		.where(eq(conversation.userId, userId));

	const convIds = convRows.map((c) => c.id);
	let msgCount = 0;

	if (convIds.length > 0) {
		const [msgResult] = await db
			.select({ count: count() })
			.from(message)
			.where(inArray(message.conversationId, convIds));
		msgCount = msgResult?.count ?? 0;
	}

	return {
		user: event.locals.user,
		conversationCount: convResult?.count ?? 0,
		messageCount: msgCount
	};
};

export const actions: Actions = {
	signOut: async (event) => {
		try {
			await auth.api.signOut({ headers: event.request.headers });
		} catch (error) {
			if (error instanceof APIError) {
				return fail(400, { message: error.message || 'Sign out failed' });
			}
			return fail(500, { message: 'Unexpected error' });
		}
		return redirect(302, '/login');
	}
};
