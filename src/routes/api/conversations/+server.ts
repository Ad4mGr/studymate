import { json } from '@sveltejs/kit';
import { db } from '$lib/server/db';
import { conversation } from '$lib/server/db/schema';
import { eq, desc } from 'drizzle-orm';

export async function GET(event) {
	if (!event.locals.user) return json({ error: 'Unauthorized' }, { status: 401 });
	const convs = await db
		.select()
		.from(conversation)
		.where(eq(conversation.userId, event.locals.user.id))
		.orderBy(desc(conversation.updatedAt));
	return json(convs);
}

export async function POST(event) {
	if (!event.locals.user) return json({ error: 'Unauthorized' }, { status: 401 });
	const id = crypto.randomUUID();
	await db.insert(conversation).values({
		id,
		userId: event.locals.user.id,
		title: 'New Chat'
	});
	const [conv] = await db.select().from(conversation).where(eq(conversation.id, id)).limit(1);
	return json(conv, { status: 201 });
}
