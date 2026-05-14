import { drizzle } from 'drizzle-orm/libsql';
import { createClient } from '@libsql/client';
import * as schema from './schema';
import { env } from '$env/dynamic/private';
import { building } from '$app/environment';

if (!env.DATABASE_URL && !building) throw new Error('DATABASE_URL is not set');

const dbUrl = env.DATABASE_URL || 'file:local.db';

const client = createClient(
	dbUrl.startsWith('file:') ? { url: dbUrl } : { url: dbUrl, authToken: env.TURSO_AUTH_TOKEN }
);

export const db = drizzle(client, { schema });
