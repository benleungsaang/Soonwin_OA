<template>
  <div class="machine-management">
    <div class="header-actions">
      <el-button type="primary" @click="showAddMachineDialog">娣诲姞鏈哄櫒</el-button>
      <JsonImportExport
        :import-function="importMachinesData"
        :export-function="exportMachinesData"
        export-file-name="machines.json"
        import-success-message="鏈哄櫒鏁版嵁瀵煎叆鎴愬姛"
        export-success-message="鏈哄櫒鏁版嵁瀵煎嚭鎴愬姛"
      />
    </div>
    <el-table :data="machines" style="width: 100%" border
    :row-style="{ cursor: 'pointer' }"
    @row-click="handleRowClick"
    >
      <el-table-column prop="thumbnail" label="璁惧缂╃暐鍥? width="120">
        <template #default="{ row }">
          <div class="image-placeholder">
            <el-icon><Picture /></el-icon>
            <span>缂╃暐鍥?/span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="model" label="璁惧鍨嬪彿" width="200" />
      <el-table-column prop="packing_speed" label="鍖呰閫熷害" width="150" />
      <el-table-column prop="show_price" label="浠锋牸" width="120" />
      <el-table-column label="鎿嶄綔" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="showEditMachineDialog(row)">缂栬緫</el-button>
          <el-button v-if="isCurrentUserAdmin" size="small" type="danger" @click="deleteMachine(row.model)">鍒犻櫎</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 鍒嗛〉 -->
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 50, 100]"
      :background="true"
      layout="total, sizes, prev, pager, next, jumper"
      :total="total"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
      style="margin-top: 20px; justify-content: center; display: flex;"
    />

    <!-- 娣诲姞/缂栬緫鏈哄櫒瀵硅瘽妗?-->
    <el-dialog
      :title="editingMachine ? '缂栬緫鏈哄櫒' : '娣诲姞鏈哄櫒'"
      v-model="showMachineDialog"
      width="60%"
      :before-close="closeMachineDialog"
    >
      <el-form
        :model="machineForm"
        :rules="machineRules"
        ref="machineFormRef"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="璁惧鍨嬪彿" prop="model">
              <el-input
                v-model="machineForm.model"
                :disabled="!!editingMachine"
                placeholder="璇疯緭鍏ヨ澶囧瀷鍙?
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="鍘熷巶鍨嬪彿" prop="original_model">
              <el-input v-model="machineForm.original_model" placeholder="璇疯緭鍏ュ師鍘傚瀷鍙? />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="鎴愭湰浠锋牸" prop="original_price">
              <el-input-number
                v-model="machineForm.original_price"
                :precision="2"
                :min="0"
                :controls=false
                style="width: 100%;"
                :disabled="!isCurrentUserAdmin"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="浠锋牸" prop="show_price">
              <el-input-number
                v-model="machineForm.show_price"
                :precision="2"
                :min="0"
                :controls=false
                style="width: 100%;"
                :disabled="!isCurrentUserAdmin"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="鍖呰閫熷害" prop="packing_speed">
              <el-input v-model="machineForm.packing_speed" placeholder="璇疯緭鍏ュ寘瑁呴€熷害" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="鎬诲姛鐜? prop="general_power">
              <el-input v-model="machineForm.general_power" placeholder="璇疯緭鍏ユ€诲姛鐜? />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="渚涚數瑙勬牸" prop="power_supply">
              <el-input v-model="machineForm.power_supply" placeholder="璇疯緭鍏ヤ緵鐢佃鏍? />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姘旀簮瑕佹眰" prop="air_source">
              <el-input v-model="machineForm.air_source" placeholder="璇疯緭鍏ユ皵婧愯姹? />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="璁惧閲嶉噺" prop="machine_weight">
              <el-input v-model="machineForm.machine_weight" placeholder="璇疯緭鍏ヨ澶囬噸閲? />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="璁惧灏哄" prop="dimensions">
              <el-input v-model="machineForm.dimensions" placeholder="璇疯緭鍏ヨ澶囧昂瀵? />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="鍖呰鏉愭枡" prop="package_material">
              <el-input v-model="machineForm.package_material" placeholder="璇疯緭鍏ュ寘瑁呮潗鏂? />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="缂╃暐鍥捐矾寰? prop="image">
              <el-input v-model="machineForm.image" placeholder="璇疯緭鍏ョ缉鐣ュ浘璺緞" />
            </el-form-item>
          </el-col>
          <el-col
            v-for="(attr, index) in customAttributes"
            :key="index" :span="12">
              <el-form-item :label="attrConfig[attr.key]?.label || attr.key">
              <el-input
                v-model="attr.value"
                :placeholder="attrConfig[attr.key]?.placeholder || `璇疯緭鍏?{attr.key}`"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="琚坊鍔犳鏁? prop="added_count">
              <el-span>{{ machineForm.added_count }} 娆?/el-span>
            </el-form-item>
          </el-col>
          <!-- <el-col :span="24">
            <el-button @click="addCustomAttribute" style="margin-top: 10px;">
              <el-icon><Plus /></el-icon>
              娣诲姞鑷畾涔夊睘鎬?            </el-button>
          </el-col> -->
          <!-- <el-col :span="24">
            <el-form-item label="鑷畾涔夊睘鎬?>
              <div class="custom-attributes-section">
                <div
                  v-for="(attr, index) in customAttributes"
                  :key="index"
                  class="custom-attribute-item"
                >
                  <el-input
                    v-model="attr.key"
                    placeholder="灞炴€у悕"
                    style="width: 200px; margin-right: 10px;"
                  />
                  <el-input
                    v-model="attr.value"
                    placeholder="灞炴€у€?
                    style="width: 200px; margin-right: 10px;"
                  />
                  <el-button
                    type="danger"
                    size="small"
                    @click="removeCustomAttribute(index)"
                  >
                    鍒犻櫎
                  </el-button>
                </div>
                <el-button @click="addCustomAttribute" style="margin-top: 10px;">
                  <el-icon><Plus /></el-icon>
                  娣诲姞鑷畾涔夊睘鎬?                </el-button>
              </div>
            </el-form-item>
          </el-col> -->
        </el-row>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeMachineDialog">鍙栨秷</el-button>
          <el-button type="primary" @click="saveMachine">纭畾</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Picture } from '@element-plus/icons-vue'
import { getMachines, createMachine, updateMachine, deleteMachine as deleteMachineAPI, importMachines, importMachinesJson, exportMachinesJson } from '@/utils/request'
import JsonImportExport from '@/components/JsonImportExport.vue'

// 鍝嶅簲寮忔暟鎹?const machines = ref<any[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 瀵硅瘽妗嗙浉鍏?const showMachineDialog = ref(false)
const editingMachine = ref<any>(null)
const machineFormRef = ref()
const machineForm = reactive({
  model: '',
  original_model: '',
  packing_speed: '',
  general_power: '',
  power_supply: '',
  air_source: '',
  machine_weight: '',
  dimensions: '',
  package_material: '',
  image: '',
  added_count: 0,
  original_price: null as number | null,
  show_price: null as number | null,
  custom_attrs: ''
})

const props = defineProps({
  // 鏄惁涓虹鐞嗗憳
  isCurrentUserAdmin: {
    type: Boolean,
    required: true, // 蹇呭～锛岀‘淇濈埗缁勪欢浼犻€?    default: false  // 榛樿鍊硷紙闃叉鏈紶閫掓椂鍑洪敊锛?  },
  // 鏄惁鐧诲綍锛堟湁token锛?  hasToken: {
    type: Boolean,
    required: true,
    default: false
  }
});

// 鑷畾涔夊睘鎬х浉鍏?const customAttributes = ref<{ key: string; value: string }[]>([])

// 琛ㄥ崟楠岃瘉瑙勫垯
const machineRules = {
  model: [
    { required: true, message: '璇疯緭鍏ヨ澶囧瀷鍙?, trigger: 'blur' },
    { min: 1, max: 100, message: '闀垮害鍦?1 鍒?100 涓瓧绗?, trigger: 'blur' }
  ]
}

// 鑾峰彇鏈哄櫒鍒楄〃
const fetchMachines = async () => {
  loading.value = true
  try {
    const response: any = await getMachines({
      page: currentPage.value,
      per_page: pageSize.value
    })
    // 娣诲姞瀹夊叏妫€鏌ワ紝纭繚response瀛樺湪涓斾负瀵硅薄
    if (response && typeof response === 'object') {
      machines.value = response.machines || []
      total.value = response.total || 0
    } else {
      console.error('API鍝嶅簲鏍煎紡閿欒:', response)
      ElMessage.error('API鍝嶅簲鏍煎紡閿欒')
      machines.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('鑾峰彇鏈哄櫒鍒楄〃澶辫触:', error)
    ElMessage.error('鑾峰彇鏈哄櫒鍒楄〃澶辫触')
    machines.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 瀹氫箟琛岀偣鍑诲鐞嗗嚱鏁?const handleRowClick = (row) => {
  // 璋冪敤缂栬緫寮圭獥鏂规硶锛屽拰缂栬緫鎸夐挳閫昏緫涓€鑷?  showEditMachineDialog(row);
};

// 鏄剧ず娣诲姞鏈哄櫒瀵硅瘽妗?const showAddMachineDialog = () => {
  editingMachine.value = null
  Object.keys(machineForm).forEach(key => {
    if (key === 'added_count') {
      (machineForm as any)[key] = 0
    } else if (key === 'original_price' || key === 'show_price') {
      (machineForm as any)[key] = null
    } else {
      (machineForm as any)[key] = ''
    }
  })
  customAttributes.value = []
  showMachineDialog.value = true
}

// 鏄剧ず缂栬緫鏈哄櫒瀵硅瘽妗?const showEditMachineDialog = (machine: any) => {
  editingMachine.value = { ...machine }
  Object.keys(machineForm).forEach(key => {
    if (key === 'custom_attrs') {
      // 涓嶅鐞哻ustom_attrs瀛楁锛岃€屾槸鍗曠嫭澶勭悊
    } else if (key === 'added_count' || key === 'original_price' || key === 'show_price') {
      // 纭繚鏁板€煎瓧娈垫槸鏁板瓧绫诲瀷
      const value = machine[key];
      (machineForm as any)[key] = value === null || value === undefined ? null : Number(value);
    } else {
      (machineForm as any)[key] = machine[key]
    }
  })

  // 澶勭悊鑷畾涔夊睘鎬?  customAttributes.value = []
  if (machine.custom_attrs) {
    try {
      const customAttrsObj = typeof machine.custom_attrs === 'string'
        ? JSON.parse(machine.custom_attrs)
        : machine.custom_attrs

      if (typeof customAttrsObj === 'object' && customAttrsObj !== null) {
        customAttributes.value = Object.entries(customAttrsObj).map(([key, value]) => ({
          key,
          value: String(value)
        }))
      }
    } catch (e) {
      console.error('瑙ｆ瀽鑷畾涔夊睘鎬уけ璐?', e)
      // 濡傛灉瑙ｆ瀽澶辫触锛屽皾璇曠洿鎺ヤ娇鐢ㄥ璞?      if (typeof machine.custom_attrs === 'object' && machine.custom_attrs !== null) {
        customAttributes.value = Object.entries(machine.custom_attrs).map(([key, value]) => ({
          key,
          value: String(value)
        }))
      }
    }
  }

  showMachineDialog.value = true
}

// 淇濆瓨鏈哄櫒
const saveMachine = async () => {
  if (!machineFormRef.value) return

  try {
    await machineFormRef.value.validate()

    // 鏋勫缓鑷畾涔夊睘鎬у璞?    const customAttrsObj: Record<string, string> = {}
    customAttributes.value.forEach(attr => {
      if (attr.key.trim()) {
        customAttrsObj[attr.key.trim()] = attr.value.trim()
      }
    })

    // 灏嗚嚜瀹氫箟灞炴€ц浆鎹负JSON瀛楃涓?    const customAttrsString = Object.keys(customAttrsObj).length > 0
      ? JSON.stringify(customAttrsObj)
      : ''

    // 鍒涘缓瑕佷繚瀛樼殑鏁版嵁瀵硅薄锛岀‘淇濇暟鍊煎瓧娈电被鍨嬫纭?    const machineData = {
      ...machineForm,
      added_count: machineForm.added_count !== null && machineForm.added_count !== undefined ? Number(machineForm.added_count) : null,
      original_price: machineForm.original_price !== null && machineForm.original_price !== undefined ? Number(machineForm.original_price) : null,
      show_price: machineForm.show_price !== null && machineForm.show_price !== undefined ? Number(machineForm.show_price) : null,
      custom_attrs: customAttrsString
    }

    if (editingMachine.value) {
      // 鏇存柊鏈哄櫒
      await updateMachine(editingMachine.value.model, machineData)
      ElMessage.success('鏈哄櫒鏇存柊鎴愬姛')
    } else {
      // 鍒涘缓鏈哄櫒
      await createMachine(machineData)
      ElMessage.success('鏈哄櫒鍒涘缓鎴愬姛')
    }

    showMachineDialog.value = false
    fetchMachines()
  } catch (error) {
    console.error('淇濆瓨鏈哄櫒澶辫触:', error)
    if (error !== true) { // Element Plus楠岃瘉澶辫触鏃朵細杩斿洖true
      ElMessage.error('淇濆瓨鏈哄櫒澶辫触')
    }
  }
}

// 娣诲姞鑷畾涔夊睘鎬?const addCustomAttribute = () => {
  customAttributes.value.push({ key: '', value: '' })
}

// 鍒犻櫎鑷畾涔夊睘鎬?const removeCustomAttribute = (index: number) => {
  customAttributes.value.splice(index, 1)
}

// 鍏抽棴瀵硅瘽妗?const closeMachineDialog = () => {
  showMachineDialog.value = false
  editingMachine.value = null
  // 娓呯┖鑷畾涔夊睘鎬?  customAttributes.value = []
}

// 鍒犻櫎鏈哄櫒
const deleteMachine = async (model: string) => {
  try {
    await ElMessageBox.confirm(
      `纭畾瑕佸垹闄ゅ瀷鍙蜂负 ${model} 鐨勬満鍣ㄥ悧锛焋,
      '纭鍒犻櫎',
      {
        confirmButtonText: '纭畾',
        cancelButtonText: '鍙栨秷',
        type: 'warning'
      }
    )

    await deleteMachineAPI(model)
    ElMessage.success('鏈哄櫒鍒犻櫎鎴愬姛')
    fetchMachines()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('鍒犻櫎鏈哄櫒澶辫触:', error)
      ElMessage.error('鍒犻櫎鏈哄櫒澶辫触')
    }
  }
}

// 澶勭悊鍒嗛〉
const handleSizeChange = (size: number) => {
  pageSize.value = size
  fetchMachines()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchMachines()
}

// 瀵煎叆鏈哄櫒鏁版嵁
const importMachinesData = async (jsonData: any) => {
  try {
    // 纭繚jsonData鏄暟缁勬牸寮?    let dataToImport = jsonData;
    if (!Array.isArray(jsonData)) {
      if (typeof jsonData === 'object' && jsonData !== null) {
        // 濡傛灉鏄崟涓璞★紝杞崲涓烘暟缁?        dataToImport = [jsonData];
      } else {
        throw new Error('JSON鏁版嵁鏍煎紡涓嶆纭紝搴斾负瀵硅薄鎴栧璞℃暟缁?);
      }
    }

    // 鐩存帴鍙戦€丣SON鏁版嵁鍒版柊鐨凙PI绔偣
    const response: any = await importMachinesJson(dataToImport);
    ElMessage.success(response.message || '鏈哄櫒鏁版嵁瀵煎叆鎴愬姛');

    // 鍒锋柊鍒楄〃
    fetchMachines();
    return response;
  } catch (error) {
    console.error('瀵煎叆鏈哄櫒鏁版嵁澶辫触:', error);
    ElMessage.error('瀵煎叆鏈哄櫒鏁版嵁澶辫触');
    throw error;
  }
};

// 瀵煎嚭鏈哄櫒鏁版嵁
const exportMachinesData = async () => {
  try {
    // 浣跨敤鏂扮殑鐩存帴JSON瀵煎嚭API
    const response: any = await exportMachinesJson();

    return response.data || [];
  } catch (error) {
    console.error('瀵煎嚭鏈哄櫒鏁版嵁澶辫触:', error);
    ElMessage.error('瀵煎嚭鏈哄櫒鏁版嵁澶辫触');
    throw error;
  }
};

// 璁惧宸紓鍖栧弬鏁伴厤缃紙鍓旈櫎鍏ㄩ噺閲嶅瀛楁锛?const attrConfig = {
  working_stations: {
    label: '宸ヤ綅鏁?,
    placeholder: '璇疯緭鍏ュ伐浣滃伐浣嶆暟閲忥紙濡?/8/10锛?
  },
  packing_speed: {
    label: '鍖呰閫熷害',
    placeholder: '璇疯緭鍏ュ寘瑁呴€熷害锛堝鈮?0pouches/min锛?
  },
  bagsize_length: {
    label: '鍖呰琚嬮暱搴?,
    placeholder: '璇疯緭鍏ュ寘瑁呰闀垮害锛堝L鈮?60mm锛?
  },
  bagsize_width: {
    label: '鍖呰琚嬪搴?,
    placeholder: '璇疯緭鍏ュ寘瑁呰瀹藉害锛堝W70-180mm锛?
  },
  machine_weight: {
    label: '璁惧閲嶉噺',
    placeholder: '璇疯緭鍏ヨ澶囬噸閲忥紙濡?00kg锛?
  },
  dimensions: {
    label: '璁惧澶栧舰灏哄',
    placeholder: '璇疯緭鍏ヨ澶囧褰㈠昂瀵革紙濡?500x900x1150mm锛?
  },
  general_power: {
    label: '鎬诲姛鐜?,
    placeholder: '璇疯緭鍏ヨ澶囨€诲姛鐜囷紙濡?.4kW锛?
  },
  premade_bag_type: {
    label: '棰勫埗琚嬬被鍨?,
    placeholder: '璇疯緭鍏ラ鍒惰绫诲瀷锛堝Flatpouch,Stand-up Pouch绛夛級'
  },
  package_material: {
    label: '鍖呰鏉愭枡',
    placeholder: '璇疯緭鍏ュ寘瑁呮潗鏂欙紙濡係ingle layer PE, PE laminated film绛夛級'
  },
  bagging_stations: {
    label: '瑁呰宸ヤ綅鏁伴噺',
    placeholder: '璇疯緭鍏ヨ琚嬪伐浣嶆暟閲忥紙濡?0锛?
  },
  vacuumized_stations: {
    label: '鎶界湡绌哄伐浣嶆暟閲?,
    placeholder: '璇疯緭鍏ユ娊鐪熺┖宸ヤ綅鏁伴噺锛堝12锛?
  },
  open_pouch_speed: {
    label: '寮€琚嬮€熷害',
    placeholder: '璇疯緭鍏ュ紑琚嬮€熷害锛堝Max.60pouches/min锛?
  },
  sealed_pouch_speed: {
    label: '灏佽閫熷害',
    placeholder: '璇疯緭鍏ュ皝琚嬮€熷害锛堝Max.45pouches/min锛?
  },
  pouch_length: {
    label: '琚嬮暱',
    placeholder: '璇疯緭鍏ヨ闀匡紙濡?50-300mm锛?
  },
  pouch_width: {
    label: '琚嬪',
    placeholder: '璇疯緭鍏ヨ瀹斤紙濡?0-150mm锛?
  },
  pouch_height: {
    label: '琚嬮珮',
    placeholder: '璇疯緭鍏ヨ楂橈紙濡?0-90mm锛?
  },
  packing_film_width: {
    label: '鍖呰鑶滃搴?,
    placeholder: '璇疯緭鍏ュ寘瑁呰啘瀹藉害锛堝100-320mm锛?
  },
  end_sealing: {
    label: '鍒€灏佺被鍨?,
    placeholder: '璇疯緭鍏ュ垁灏佺被鍨嬶紙濡侭ox-motion Rotray-motion锛?
  },
  packaging_material: {
    label: '鍖呰鐗╂枡绫诲瀷',
    placeholder: '璇疯緭鍏ュ寘瑁呯墿鏂欑被鍨嬶紙濡侺iquid,high viscosity fluid锛?
  },
  filling_capacity: {
    label: '濉厖瀹归噺',
    placeholder: '璇疯緭鍏ュ～鍏呭閲忥紙濡?00-5000g锛?
  },
  productsizerange: {
    label: '浜у搧灏哄鑼冨洿',
    placeholder: '璇疯緭鍏ヤ骇鍝佸昂瀵歌寖鍥达紙濡侶5-60mm锛?
  },
  sealing_wheels_structure: {
    label: '瀵嗗皝杞粨鏋?,
    placeholder: '璇疯緭鍏ュ瘑灏佽疆缁撴瀯锛堝Small/Big锛?
  },
  centerdistance: {
    label: '涓績璺?,
    placeholder: '璇疯緭鍏ヤ腑蹇冭窛锛堝150mm锛?
  },
  centerdiameter: {
    label: '涓績鐩村緞',
    placeholder: '璇疯緭鍏ヤ腑蹇冪洿寰勶紙濡?20mm锛?
  }
};


// 鍒濆鍖栨暟鎹?onMounted(() => {
  fetchMachines()
})
</script>

<style scoped>
.machine-management {
  padding: 20px 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

:deep(.el-table) {
  border-radius: 4px;
}

:deep(.el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 60px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
}

.image-placeholder .el-icon {
  font-size: 20px;
  color: #8c939d;
  margin-bottom: 4px;
}

.image-placeholder span {
  font-size: 12px;
  color: #8c939d;
}

.custom-attributes-section {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  min-height: 50px;
}

.custom-attribute-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

tr.el-table__row:hover {
  cursor: pointer;
  background-color: #f5f7fa;
}
</style>
