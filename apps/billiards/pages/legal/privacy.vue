<script setup lang="ts">
useHead({ title: 'Политика конфиденциальности' })
</script>

<template>
  <main class="page-shell page-shell--narrow py-10">
    <p class="section-eyebrow">правовая информация</p>
    <h1 class="mt-2 font-display text-3xl font-bold">Политика конфиденциальности</h1>
    <p class="mt-3 text-sm text-cloth-muted">Действует для сервиса «Цифровое Сукно».</p>

    <div class="prose-legal mt-8 space-y-5 text-sm leading-relaxed text-cloth-chalk/85">
      <section>
        <h2 class="font-display text-lg font-bold">1. Какие данные мы обрабатываем</h2>
        <p class="mt-2">
          При регистрации: логин, адрес электронной почты, пароль (хранится в виде хеша), отображаемое имя,
          аватар, город, Telegram и текст «о себе», если вы их указали. При игре: история сессий и прогресс
          академии, привязанные к аккаунту. Технические данные: cookies сессии, IP и время входа в журнале
          безопасности администратора.
        </p>
      </section>
      <section>
        <h2 class="font-display text-lg font-bold">2. Зачем это нужно</h2>
        <p class="mt-2">
          Данные нужны, чтобы создать аккаунт, войти в сервис, сохранить прогресс, показать профиль другим
          участникам зала и обеспечить безопасность (подтверждение email, смена пароля, 2FA).
        </p>
      </section>
      <section>
        <h2 class="font-display text-lg font-bold">3. Cookies</h2>
        <p class="mt-2">
          Мы используем только необходимые cookies авторизации (httpOnly). Они хранят сессию входа и не
          применяются для рекламы или сторонней аналитики.
        </p>
      </section>
      <section>
        <h2 class="font-display text-lg font-bold">4. Хранение и доступ</h2>
        <p class="mt-2">
          Данные хранятся на сервере установки. Доступ к списку аккаунтов есть у администратора зала.
          Пароли в открытом виде не хранятся и не передаются.
        </p>
      </section>
      <section>
        <h2 class="font-display text-lg font-bold">5. Ваши права</h2>
        <p class="mt-2">
          Вы можете изменить имя, фото и контакты в профиле, сменить пароль и запросить удаление аккаунта
          у администратора установки.
        </p>
      </section>
      <section>
        <h2 class="font-display text-lg font-bold">6. Контакты</h2>
        <p class="mt-2">
          По вопросам персональных данных обратитесь к администратору вашего зала — через раздел «Админка»,
          если вы им являетесь, либо лично к оператору установки.
        </p>
      </section>
    </div>
  </main>
</template>
