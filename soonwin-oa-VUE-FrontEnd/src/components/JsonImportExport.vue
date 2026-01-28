<template>
  <div class="json-import-export">
    <el-upload
      class="upload-demo"
      :auto-upload="false"
      :show-file-list="false"
      accept=".json"
      :on-change="handleImport"
    >
      <el-button type="success" :icon="Upload">导入JSON</el-button>
    </el-upload>
    <el-button type="warning" :icon="Download" @click="handleExport" style="margin-left: 10px;">
      导出JSON
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Download } from '@element-plus/icons-vue'
import { ref } from 'vue'

// 定义组件的props
interface Props {
  importFunction?: (data: any) => Promise<any> // 导入数据的API函数
  exportFunction?: () => Promise<any>          // 导出数据的API函数
  exportFileName?: string                      // 导出文件名
  importSuccessMessage?: string                // 导入成功的提示信息
  exportSuccessMessage?: string                // 导出成功的提示信息
}

const props = withDefaults(defineProps<Props>(), {
  importSuccessMessage: '数据导入成功',
  exportSuccessMessage: '数据导出成功',
  exportFileName: 'data.json'
})

// 导入JSON文件
const handleImport = async (file: any) => {
  try {
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const content = e.target?.result as string
        if (!content) {
          ElMessage.error('文件内容为空')
          return
        }

        // 解析JSON
        let jsonData
        try {
          jsonData = JSON.parse(content)
        } catch (parseError) {
          ElMessage.error('JSON文件格式错误')
          return
        }

        // 验证数据格式
        if (!jsonData || (Array.isArray(jsonData) && jsonData.length === 0)) {
          ElMessage.error('JSON数据为空或格式不正确')
          return
        }

        // 如果提供了导入函数，则调用它
        if (props.importFunction) {
          await props.importFunction(jsonData)
          ElMessage.success(props.importSuccessMessage)
        } else {
          ElMessage.warning('未提供导入函数')
        }
      } catch (error) {
        console.error('处理导入文件时出错:', error)
        ElMessage.error('处理导入文件时出错')
      }
    }
    reader.readAsText(file.raw)
  } catch (error) {
    console.error('读取文件时出错:', error)
    ElMessage.error('读取文件时出错')
  }
}

// 导出JSON文件
const handleExport = async () => {
  try {
    let dataToExport: any

    // 如果提供了导出函数，则调用它获取数据
    if (props.exportFunction) {
      dataToExport = await props.exportFunction()
    } else {
      ElMessage.warning('未提供导出函数')
      return
    }

    // 将数据转换为JSON字符串
    const jsonString = JSON.stringify(dataToExport, null, 2)

    // 创建Blob对象
    const blob = new Blob([jsonString], { type: 'application/json' })

    // 创建下载链接
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = props.exportFileName

    // 触发下载
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    // 释放URL对象
    URL.revokeObjectURL(url)

    ElMessage.success(props.exportSuccessMessage)
  } catch (error) {
    console.error('导出数据时出错:', error)
    ElMessage.error('导出数据时出错')
  }
}
</script>

<style scoped>
.json-import-export {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
</style>