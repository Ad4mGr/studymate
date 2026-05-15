import { json } from '@sveltejs/kit';
import { db } from '$lib/server/db';
import { conversation } from '$lib/server/db/schema';
import { eq, desc } from 'drizzle-orm';

export async function GET(event) {
	if (!event.locals.user) return json({ error: 'Unauthorized' }, { status: 401 });
	const limit = Math.min(Number(event.url.searchParams.get('limit') ?? 50), 100);
	const convs = await db
		.select()
		.from(conversation)
		.where(eq(conversation.userId, event.locals.user.id))
		.orderBy(desc(conversation.updatedAt))
		.limit(limit);
	return json(convs);
}

export async function POST(event) {
	if (!event.locals.user) return json({ error: 'Unauthorized' }, { status: 401 });
	const [conv] = await db.insert(conversation).values({
		userId: event.locals.user.id,
		title: 'New Chat'
	}).returning();
	return json(conv, { status: 201 });
}
