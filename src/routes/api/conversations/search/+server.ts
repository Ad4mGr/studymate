import { json } from '@sveltejs/kit';
import { db } from '$lib/server/db';
import { conversation, message } from '$lib/server/db/schema';
import { eq, and, or, like, desc } from 'drizzle-orm';

export async function GET(event) {
	if (!event.locals.user) return json({ error: 'Unauthorized' }, { status: 401 });

	const q = event.url.searchParams.get('q') || '';
	if (!q.trim()) return json([]);

	const searchTerm = `%${q}%`;

	const convs = await db
		.select()
		.from(conversation)
		.where(
			and(
				eq(conversation.userId, event.locals.user.id),
				or(
					like(conversation.title, searchTerm),
				)
			)
		)
		.orderBy(desc(conversation.updatedAt))
		.limit(50);

	return json(convs);
}
