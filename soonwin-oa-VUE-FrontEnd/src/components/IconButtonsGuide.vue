<!-- 
前端图标按钮规范
用于指导后续开发中的按钮设计
遵循 Element Plus 图标规范
-->

<!-- 常规操作图标按钮规范 -->
<!-- 
对于常规操作如添加、删除、修改、查询等，使用图标按钮，格式如下：
1. 单一按钮：使用纯图标
2. 同级多按钮：使用图标加简单文字
3. 常用图标映射：
   - 添加/新增: Plus / CirclePlus / EditPen
   - 删除: Delete / DeleteFilled 
   - 修改/编辑: Edit / EditPen
   - 查询/搜索: Search / SearchInfo
   - 保存: Finished / Check
   - 取消: Close / CircleClose
   - 刷新: Refresh / RefreshRight
   - 下载: Download / Download
   - 上传: Upload / UploadFilled
   - 查看: View / Monitor
   - 设置: Setting / Tools
   - 菜单: Menu / More
-->


<!-- 示例代码 -->

<!-- 1. 纯图标按钮（单一操作） -->
<el-button type="primary" @click="addRecord">
  <el-icon><Plus /></el-icon>
</el-button>

<el-button type="danger" @click="deleteRecord">
  <el-icon><Delete /></el-icon>
</el-button>

<el-button @click="editRecord">
  <el-icon><Edit /></el-icon>
</el-button>

<el-button @click="searchRecords">
  <el-icon><Search /></el-icon>
</el-button>

<!-- 2. 图标加文字按钮（同级多按钮） -->
<el-button type="primary" @click="addRecord">
  <el-icon><Plus /></el-icon>
  添加
</el-button>

<el-button @click="editRecord">
  <el-icon><Edit /></el-icon>
  编辑
</el-button>

<el-button type="danger" @click="deleteRecord">
  <el-icon><Delete /></el-icon>
  删除
</el-button>

<!-- 3. 在表格操作列中的应用 -->
<el-table-column label="操作" width="150">
  <template #default="{ row }">
    <el-button size="small" @click="viewRecord(row)">
      <el-icon><View /></el-icon>
    </el-button>
    <el-button size="small" @click="editRecord(row)">
      <el-icon><Edit /></el-icon>
    </el-button>
    <el-button size="small" type="danger" @click="deleteRecord(row)">
      <el-icon><Delete /></el-icon>
    </el-button>
  </template>
</el-table-column>

<!-- 4. 同级多按钮（图标+文字） -->
<div class="button-group">
  <el-button type="primary" @click="saveRecord">
    <el-icon><Finished /></el-icon>
    保存
  </el-button>
  <el-button @click="cancelOperation">
    <el-icon><Close /></el-icon>
    取消
  </el-button>
  <el-button @click="resetForm">
    <el-icon><Refresh /></el-icon>
    重置
  </el-button>
</div>

<!-- 5. 常用图标映射表 -->
<!-- 
添加操作: Plus, CirclePlus, EditPen
编辑操作: Edit, EditPen, Setting
删除操作: Delete, DeleteFilled
查询操作: Search, SearchInfo
保存操作: Finished, Check, Select
取消操作: Close, CircleClose
刷新操作: Refresh, RefreshRight
上传操作: Upload, UploadFilled
下载操作: Download, Download
查看操作: View, Monitor
设置操作: Setting, Tools
菜单操作: Menu, More
信息操作: InfoFilled, Warning, QuestionFilled
-->