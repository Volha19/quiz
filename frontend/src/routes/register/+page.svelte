<script>
	let name = '';
	let email = '';
	let password = '';
	let confirmPassword = '';
	let error = '';
	let loading = false;

	async function handleSubmit() {
		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}
		loading = true;
		error = '';
		try {
			const response = await fetch('http://localhost:8000/api/auth/register/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					username: email,
					email,
					password,
					first_name: name.split(' ')[0],
					last_name: name.split(' ').slice(1).join(' ')
				}),
			});
			const data = await response.json();
			if (response.ok) {
				localStorage.setItem('access_token', data.tokens.access);
				localStorage.setItem('refresh_token', data.tokens.refresh);
				localStorage.setItem('user', JSON.stringify(data.user));
				window.location.href = '/';
			} else {
				error = Object.values(data).flat().join(', ') || 'Registration failed';
			}
		} catch (err) {
			error = 'Network error';
		}
		loading = false;
	}
</script>

<svelte:head>
	<title>Register — Quiz Maker</title>
</svelte:head>

<div class="flex-column d-flex justify-content-center align-items-center" style="min-height: 100vh">
	<h1 id="formTitle">Register</h1>
	<div class="auth-card">
		<form on:submit|preventDefault={handleSubmit}>
			<input
				type="text"
				class="form-control"
				placeholder="Full Name"
				bind:value={name}
				required
			/>
			<input
				type="email"
				class="form-control"
				placeholder="Email"
				bind:value={email}
				required
			/>
			<input
				type="password"
				class="form-control"
				placeholder="Password"
				bind:value={password}
				required
			/>
			<input
				type="password"
				class="form-control"
				placeholder="Confirm Password"
				bind:value={confirmPassword}
				required
			/>
			<button type="submit" class="cta-btn" disabled={loading}>
				{loading ? 'Registering...' : 'Register'}
			</button>
			{#if error}
				<div style="color: #d32f2f; margin-top: 12px; text-align: center;">{error}</div>
			{/if}
			<p class="mt-3">
				Already have an account?
				<a href="/login" class="toggle-link">Log In</a>
			</p>
		</form>
	</div>
</div>