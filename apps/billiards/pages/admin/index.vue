<script setup lang="ts">
useHead({ title: 'Админка' })
</script>

<template>
  <AdminShell>
    <div class="grid gap-4 md:grid-cols-2">
      <NuxtLink to="/admin/seo" class="card-surface block p-5 transition hover:border-cloth-accent/50">
        <p class="text-xs uppercase tracking-[0.2em] text-cloth-accent">сайт</p>
        <h2 class="mt-2 font-display text-xl font-bold">SEO и тексты</h2>
        <p class="mt-2 text-sm text-cloth-muted">
          Title, description, keywords, канонический URL, OG-картинка, слоган и сообщение на главной.
        </p>
      </NuxtLink>
      <NuxtLink to="/admin/users" class="card-surface block p-5 transition hover:border-cloth-accent/50">
        <p class="text-xs uppercase tracking-[0.2em] text-cloth-accent">доступ</p>
        <h2 class="mt-2 font-display text-xl font-bold">Пользователи и роли</h2>
        <p class="mt-2 text-sm text-cloth-muted">
          Аккаунты операторов и игроков, роли admin / operator / player, блокировка.
        </p>
      </NuxtLink>
      <NuxtLink to="/admin/audit" class="card-surface block p-5 transition hover:border-cloth-accent/50">
        <p class="text-xs uppercase tracking-[0.2em] text-cloth-accent">безопасность</p>
        <h2 class="mt-2 font-display text-xl font-bold">Журнал действий</h2>
        <p class="mt-2 text-sm text-cloth-muted">
          История смены ролей, правок SEO и входа по legacy-ключу.
        </p>
      </NuxtLink>
      <NuxtLink to="/admin/security" class="card-surface block p-5 transition hover:border-cloth-accent/50">
        <p class="text-xs uppercase tracking-[0.2em] text-cloth-accent">2FA</p>
        <h2 class="mt-2 font-display text-xl font-bold">Двухфакторный вход</h2>
        <p class="mt-2 text-sm text-cloth-muted">
          TOTP для operator и admin — Google Authenticator, Authy и аналоги.
        </p>
      </NuxtLink>
    </div>
  </AdminShell>
</template>
