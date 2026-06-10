<template>
  <div class="min-h-screen gradient-bg flex items-center justify-center p-4">
    <div class="text-center">
      <div class="text-9xl text-love love-heart mb-4">
        <el-icon><QuestionFilled /></el-icon>
      </div>
      <h1 class="text-6xl font-bold text-gray-800 mb-4">404</h1>
      <p class="text-xl text-gray-600 mb-8">抱歉，您访问的页面不存在</p>
      <el-button
        type="primary"
        size="large"
        class="!bg-love !border-love hover:!bg-love-dark"
        @click="$router.push('/')"
      >
        <el-icon class="mr-1"><HomeFilled /></el-icon>
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>
