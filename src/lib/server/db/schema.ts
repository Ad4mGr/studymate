import { integer, sqliteTable, text, index } from 'drizzle-orm/sqlite-core';

export const task = sqliteTable('task', {
	id: text('id')
		.primaryKey()
		.$defaultFn(() => crypto.randomUUID()),
	title: text('title').notNull(),
	priority: integer('priority').notNull().default(1)
});

export const conversation = sqliteTable('conversation', {
	id: text('id')
		.primaryKey()
		.$defaultFn(() => crypto.randomUUID()),
	userId: text('user_id').notNull(),
	title: text('title').notNull().default('New Chat'),
	createdAt: text('created_at')
		.notNull()
		.$defaultFn(() => new Date().toISOString()),
	updatedAt: text('updated_at')
		.notNull()
		.$defaultFn(() => new Date().toISOString())
}, (table) => ({
	userIdIdx: index('conversation_user_id_idx').on(table.userId),
	updatedAtIdx: index('conversation_updated_at_idx').on(table.updatedAt),
}));

export const message = sqliteTable('message', {
	id: text('id')
		.primaryKey()
		.$defaultFn(() => crypto.randomUUID()),
	conversationId: text('conversation_id').notNull().references(() => conversation.id, { onDelete: 'cascade' }),
	role: text('role', { enum: ['user', 'assistant'] }).notNull(),
	content: text('content').notNull(),
	createdAt: text('created_at')
		.notNull()
		.$defaultFn(() => new Date().toISOString())
}, (table) => ({
	conversationIdIdx: index('message_conversation_id_idx').on(table.conversationId),
}));

export * from './auth.schema';
