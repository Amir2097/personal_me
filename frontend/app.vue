<template>
  <BrandWatermark />
  <div class="brand-stamp-bar">
    <BrandStamp variant="pill" />
  </div>
  <div class="relative z-[1] min-h-screen pt-7">
    <TerminalMatrixOverlay />
    <CookieNotice />
    <NuxtPage />
  </div>
</template>
