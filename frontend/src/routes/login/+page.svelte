<script>
	let email = '';
	let password = '';
	let error = '';
	let loading = false;

	async function handleSubmit() {
		loading = true;
		error = '';
		try {
			const response = await fetch('http://localhost:8000/api/auth/login/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ username: email, password }),
			});
			const data = await response.json();
			if (response.ok) {
				localStorage.setItem('access_token', data.tokens.access);
				localStorage.setItem('refresh_token', data.tokens.refresh);
				localStorage.setItem('user', JSON.stringify(data.user));
				window.location.href = '/';
			} else {
				error = data.detail || 'Login failed';
			}
		} catch (err) {
			error = 'Network error';
		}
		loading = false;
	}
</script>

<svelte:head>
	<title>Log In — Quiz Maker</title>
</svelte:head>

<div class="flex-column d-flex justify-content-center align-items-center" style="min-height: 100vh">
	<h1 id="formTitle">Log In</h1>
	<div class="auth-card">
		<form on:submit|preventDefault={handleSubmit}>
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
			<button type="submit" class="cta-btn" disabled={loading}>
				{loading ? 'Signing in...' : 'Log In'}
			</button>
			{#if error}
				<div style="color: #d32f2f; margin-top: 12px; text-align: center;">{error}</div>
			{/if}
			<p class="mt-3">
				Don't have an account?
				<a href="/register" class="toggle-link">Register</a>
			</p>
		</form>
	</div>
</div>