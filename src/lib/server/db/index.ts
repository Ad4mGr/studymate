import { drizzle } from 'drizzle-orm/libsql';
import { createClient } from '@libsql/client';
import * as schema from './schema';
import { env } from '$env/dynamic/private';

if (!env.DATABASE_URL) throw new Error('DATABASE_URL is not set');

const client = createClient(
	env.DATABASE_URL.startsWith('file:')
		? { url: env.DATABASE_URL }
		: { url: env.DATABASE_URL, authToken: env.TURSO_AUTH_TOKEN }
);

export const db = drizzle(client, { schema });
