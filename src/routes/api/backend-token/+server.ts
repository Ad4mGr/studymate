import { json } from '@sveltejs/kit';
import { SignJWT } from 'jose';
import { env } from '$env/dynamic/private';

export async function GET(event) {
	if (!event.locals.user) return json({ error: 'Unauthorized' }, { status: 401 });

	const secret = new TextEncoder().encode(env.BACKEND_JWT_SECRET || env.BETTER_AUTH_SECRET);
	const token = await new SignJWT({ user_id: event.locals.user.id })
		.setProtectedHeader({ alg: 'HS256' })
		.setIssuedAt()
		.setExpirationTime('1h')
		.sign(secret);

	return json({ token });
}
