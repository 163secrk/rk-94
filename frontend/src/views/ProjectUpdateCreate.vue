<template>
  <div class="max-w-4xl mx-auto">
    <el-page-header
      class="mb-6"
      content="返回我的项目"
      @back="$router.push('/projects/my')"
    />

    <div class="bg-white rounded-xl p-8 card-shadow">
      <h2 class="text-2xl font-bold text-gray-800 mb-2 flex items-center">
        <el-icon class="text-love mr-2"><Edit /></el-icon>
        发布项目进展
      </h2>
      <p class="text-gray-500 mb-8">定期向您的捐赠人分享项目最新动态，让爱心传递更透明</p>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        label-position="top"
      >
        <el-form-item label="选择项目" prop="project">
          <el-select
            v-model="form.project"
            placeholder="请选择要发布进展的项目"
            class="w-full"
            size="large"
          >
            <el-option
              v-for="p in availableProjects"
              :key="p.id"
              :label="p.title"
              :value="p.id"
            >
              <div class="flex items-center">
                <span>{{ p.title }}</span>
                <el-tag size="small" :type="statusTagType(p.status)" class="ml-2">
                  {{ p.status_display }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="动态标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请输入动态标题，例如：第一批物资已送达"
            maxlength="200"
            show-word-limit
            size="large"
          />
        </el-form-item>

        <el-form-item label="动态内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            placeholder="请详细描述项目的最新进展情况..."
            :rows="8"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="上传图片">
          <el-upload
            v-model:file-list="imageList"
            list-type="picture-card"
            :auto-upload="false"
            :on-preview="handleImagePreview"
            :on-remove="handleImageRemove"
            :limit="9"
            accept="image/*"
            multiple
          >
            <el-icon><Plus /></el-icon>
            <template #tip>
              <div class="el-upload__tip text-xs text-gray-400 mt-1">
                最多上传9张图片，支持 jpg/png/gif 格式
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="上传视频">
          <el-upload
            v-model:file-list="videoList"
            :auto-upload="false"
            :on-remove="handleVideoRemove"
            :limit="3"
            accept="video/*"
            multiple
          >
            <el-button type="primary" :icon="VideoCamera">选择视频</el-button>
            <template #tip>
              <div class="el-upload__tip text-xs text-gray-400 mt-1">
                最多上传3个视频文件
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <div class="flex gap-4">
            <el-button
              type="primary"
              size="large"
              class="!bg-love !border-love hover:!bg-love-dark"
              :loading="submitting"
              @click="handleSubmit"
            >
              <el-icon class="mr-1"><Promotion /></el-icon>
              发布动态
            </el-button>
            <el-button size="large" @click="$router.push('/projects/my')">
              取消
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <el-dialog v-model="previewVisible" title="图片预览" width="80%">
      <img :src="previewImage" style="width: 100%" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getMyProjects, createProjectUpdate } from '@/api/projects'
import type { Project, ProjectUpdateCreateForm } from '@/types'
import { ElMessage, type FormInstance, type FormRules, type UploadFile, type UploadUserFile } from 'element-plus'
import { Edit, Plus, VideoCamera, Promotion } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const myProjects = ref<Project[]>([])
const imageList = ref<UploadUserFile[]>([])
const videoList = ref<UploadUserFile[]>([])
const previewVisible = ref(false)
const previewImage = ref('')

const form = reactive<ProjectUpdateCreateForm>({
  project: 0,
  title: '',
  content: '',
})

const rules: FormRules = {
  project: [{ required: true, message: '请选择项目', trigger: 'change' }],
  title: [{ required: true, message: '请输入动态标题', trigger: 'blur' }],
  content: [
    {
      validator: (_rule, value, callback) => {
        if (!value?.trim() && imageList.value.length === 0 && videoList.value.length === 0) {
          callback(new Error('至少需要填写文字内容或上传图片/视频'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const availableProjects = computed(() => {
  return myProjects.value.filter(p =>
    ['funding', 'executing', 'completed'].includes(p.status)
  )
})

const statusTagType = (status: string) => {
  switch (status) {
    case 'funding': return 'success'
    case 'completed': return 'info'
    case 'executing': return 'primary'
    default: return 'warning'
  }
}

const handleImagePreview = (file: UploadFile) => {
  previewImage.value = file.url!
  previewVisible.value = true
}

const handleImageRemove = () => {}

const handleVideoRemove = () => {}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()

  submitting.value = true
  try {
    const formData = new FormData()
    formData.append('project', String(form.project))
    formData.append('title', form.title)
    formData.append('content', form.content)

    imageList.value.forEach((file) => {
      if (file.raw) {
        formData.append('images', file.raw)
      }
    })

    videoList.value.forEach((file) => {
      if (file.raw) {
        formData.append('videos', file.raw)
      }
    })

    await createProjectUpdate(formData)
    ElMessage.success('项目进展发布成功，已通知所有捐赠人！')
    router.push('/projects/my')
  } catch (error) {
    console.error('Create project update error:', error)
  } finally {
    submitting.value = false
  }
}

const fetchMyProjects = async () => {
  try {
    const res = await getMyProjects()
    myProjects.value = res
    if (availableProjects.value.length > 0 && !form.project) {
      form.project = availableProjects.value[0].id
    }
  } catch (error) {
    console.error('Fetch my projects error:', error)
  }
}

onMounted(() => {
  fetchMyProjects()
})
</script>
