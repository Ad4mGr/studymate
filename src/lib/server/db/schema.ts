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

export const flashcard = sqliteTable('flashcard', {
	id: text('id')
		.primaryKey()
		.$defaultFn(() => crypto.randomUUID()),
	courseId: text('course_id').notNull(),
	userId: text('user_id').notNull(),
	front: text('front').notNull(),
	back: text('back').notNull(),
	nextReviewDate: text('next_review_date')
		.notNull()
		.$defaultFn(() => new Date().toISOString()),
	createdAt: text('created_at')
		.notNull()
		.$defaultFn(() => new Date().toISOString())
}, (table) => ({
	courseIdIdx: index('flashcard_course_id_idx').on(table.courseId),
	userIdIdx: index('flashcard_user_id_idx').on(table.userId),
}));

export const quiz = sqliteTable('quiz', {
	id: text('id')
		.primaryKey()
		.$defaultFn(() => crypto.randomUUID()),
	courseId: text('course_id').notNull(),
	userId: text('user_id').notNull(),
	score: integer('score').notNull().default(0),
	total: integer('total').notNull().default(0),
	feedback: text('feedback').default(''),
	state: text('state', { enum: ['in_progress', 'completed'] }).notNull().default('in_progress'),
	currentQuestion: integer('current_question').notNull().default(0),
	createdAt: text('created_at')
		.notNull()
		.$defaultFn(() => new Date().toISOString()),
	updatedAt: text('updated_at')
		.notNull()
		.$defaultFn(() => new Date().toISOString())
}, (table) => ({
	courseIdIdx: index('quiz_course_id_idx').on(table.courseId),
	userIdIdx: index('quiz_user_id_idx').on(table.userId),
}));

export const quizAnswer = sqliteTable('quiz_answer', {
	id: text('id')
		.primaryKey()
		.$defaultFn(() => crypto.randomUUID()),
	quizId: text('quiz_id').notNull().references(() => quiz.id, { onDelete: 'cascade' }),
	question: text('question').notNull(),
	userAnswer: text('user_answer').notNull(),
	correct: integer('correct').notNull(),
	explanation: text('explanation').notNull(),
	createdAt: text('created_at')
		.notNull()
		.$defaultFn(() => new Date().toISOString())
}, (table) => ({
	quizIdIdx: index('quiz_answer_quiz_id_idx').on(table.quizId),
}));

export * from './auth.schema';
