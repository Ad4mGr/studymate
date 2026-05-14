import { json } from '@sveltejs/kit';
import { db } from '$lib/server/db';
import { conversation } from '$lib/server/db/schema';
import { eq, and } from 'drizzle-orm';

export async function GET(event) {
	if (!event.locals.user) return json({ error: 'Unauthorized' }, { status: 401 });
	const [conv] = await db
		.select()
		.from(conversation)
		.where(and(eq(conversation.id, event.params.id), eq(conversation.userId, event.locals.user.id)))
		.limit(1);
	if (!conv) return json({ error: 'Not found' }, { status: 404 });
	return json(conv);
}

export async function PATCH(event) {
	if (!event.locals.user) return json({ error: 'Unauthorized' }, { status: 401 });
	const body: { title?: string } = await event.request.json();
	await db
		.update(conversation)
		.set({ title: body.title, updatedAt: new Date().toISOString() })
		.where(and(eq(conversation.id, event.params.id), eq(conversation.userId, event.locals.user.id)));
	const [conv] = await db.select().from(conversation).where(eq(conversation.id, event.params.id)).limit(1);
	if (!conv) return json({ error: 'Not found' }, { status: 404 });
	return json(conv);
}

export async function DELETE(event) {
	if (!event.locals.user) return json({ error: 'Unauthorized' }, { status: 401 });
	await db
		.delete(conversation)
		.where(and(eq(conversation.id, event.params.id), eq(conversation.userId, event.locals.user.id)));
	return new Response(null, { status: 204 });
}
