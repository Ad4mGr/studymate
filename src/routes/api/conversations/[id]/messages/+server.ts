import { json } from '@sveltejs/kit';
import { db } from '$lib/server/db';
import { message, conversation } from '$lib/server/db/schema';
import { eq, asc } from 'drizzle-orm';

export async function GET(event) {
	if (!event.locals.user) return json({ error: 'Unauthorized' }, { status: 401 });
	const msgs = await db
		.select()
		.from(message)
		.where(eq(message.conversationId, event.params.id))
		.orderBy(asc(message.createdAt));
	return json(msgs);
}

export async function POST(event) {
	if (!event.locals.user) return json({ error: 'Unauthorized' }, { status: 401 });
	const body: { role: 'user' | 'assistant'; content: string } = await event.request.json();
	const id = crypto.randomUUID();
	await db.insert(message).values({
		id,
		conversationId: event.params.id,
		role: body.role,
		content: body.content
	});
	await db
		.update(conversation)
		.set({ updatedAt: new Date().toISOString() })
		.where(eq(conversation.id, event.params.id));
	const [msg] = await db.select().from(message).where(eq(message.id, id)).limit(1);
	return json(msg, { status: 201 });
}
