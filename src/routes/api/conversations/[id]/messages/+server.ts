import { json } from '@sveltejs/kit';
import { db } from '$lib/server/db';
import { message, conversation } from '$lib/server/db/schema';
import { eq, asc } from 'drizzle-orm';

export async function GET(event) {
	if (!event.locals.user) return json({ error: 'Unauthorized' }, { status: 401 });
	const limit = Math.min(Number(event.url.searchParams.get('limit') ?? 100), 500);
	const msgs = await db
		.select()
		.from(message)
		.where(eq(message.conversationId, event.params.id))
		.orderBy(asc(message.createdAt))
		.limit(limit);
	return json(msgs);
}

export async function POST(event) {
	if (!event.locals.user) return json({ error: 'Unauthorized' }, { status: 401 });
	const body: { role: 'user' | 'assistant'; content: string } = await event.request.json();
	const now = new Date().toISOString();
	const [msg] = await db.insert(message).values({
		conversationId: event.params.id,
		role: body.role,
		content: body.content
	}).returning();
	await db
		.update(conversation)
		.set({ updatedAt: now })
		.where(eq(conversation.id, event.params.id));
	return json(msg, { status: 201 });
}
