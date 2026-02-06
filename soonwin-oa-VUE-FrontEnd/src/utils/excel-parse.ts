/**
 * JSON/Excel数据解析工具
 * 用于解析和匹配JSON/Excel格式的数据到文件
 */

export interface MatchData {
  filename: string;
  title: string;
  machineId: string;
  tags: string;
  remark: string;
}

export interface MatchResult {
  file: any;
  data: MatchData;
}

export interface ParseResult {
  matchedFiles: MatchResult[];
  unmatchedFiles: string[];
  isMatched: boolean;
}

/**
 * 解析JSON/表格格式的文本数据
 * @param inputText - 输入的文本数据，格式为：照片文件名	照片标题	关联机器	标签	备注
 * @param fileList - 文件列表
 * @returns 解析结果，包含匹配的文件、未匹配的文件和是否匹配成功的状态
 */
export const parseJsonToFiles = (inputText: string, fileList: any[]): ParseResult => {
  try {
    if (!inputText?.trim()) {
      throw new Error('请输入匹配信息');
    }

    // 第一步：将所有连续空白（制表符、多个空格、全角空格）统一替换为单个制表符
    const normalizedText = inputText.replace(/[\s\u00A0]+/g, '\t');
    // 第二步：按换行符分割行（兼容\r\n和\n）
    let lines = normalizedText.split(/\r?\n/).filter(line => line.trim() !== '');

    // 核心修复：处理无换行符的场景（所有内容在一行）
    if (lines.length === 1) {
      const allFields = lines[0].split('\t').map(field => field.trim()).filter(field => field);
      // 检查是否是表头+多行数据混在一起的情况（表头5个字段，总字段数>5且能被5整除）
      if (allFields.length >= 5 && allFields.slice(0, 5).join(',') === '照片文件名,照片标题,关联机器,标签,备注') {
        // 分离表头和数据
        const headerFields = allFields.slice(0, 5); // 前5个是表头
        const dataFields = allFields.slice(5);     // 后面的是数据

        // 按每5个字段为一行拆分数据
        const newLines = [headerFields.join('\t')]; // 重新构建表头行
        for (let i = 0; i < dataFields.length; i += 5) {
          const rowFields = dataFields.slice(i, i + 5);
          if (rowFields.length >= 1) { // 至少有文件名字段
            newLines.push(rowFields.join('\t'));
          }
        }
        lines = newLines; // 使用重构后的行数据
      }
    }

    if (lines.length === 0) {
      throw new Error('请输入匹配信息');
    }

    // 解析表头
    const headers = lines[0].split('\t').map(header => header.trim());

    // 校验表头（增加容错性，处理大小写和空白问题）
    if (headers.length < 5 ||
        headers[0].toLowerCase().trim() !== '照片文件名' ||
        headers[1].toLowerCase().trim() !== '照片标题' ||
        headers[2].toLowerCase().trim() !== '关联机器' ||
        headers[3].toLowerCase().trim() !== '标签' ||
        headers[4].toLowerCase().trim() !== '备注') {
      throw new Error('表头格式不正确，请使用：照片文件名\t照片标题\t关联机器\t标签\t备注');
    }

    // 解析数据行
    const dataRows: MatchData[] = lines.slice(1).map(line => {
      const fields = line.split('\t').map(field => field.trim());
      // 确保至少有文件名字段，其他字段可选（补空）
      if (fields.length >= 1 && fields[0]) {
        return {
          filename: fields[0] || '',
          title: fields[1] || '',
          machineId: fields[2] || '',
          tags: fields[3] || '',
          remark: fields[4] || ''
        };
      }
      return null;
    }).filter(row => row !== null) as MatchData[];

    // 匹配文件与数据
    const matchedFiles: MatchResult[] = [];
    const unmatchedFiles: string[] = [];

    fileList.forEach(fileObj => {
      const originalFilename = fileObj.name;
      // 安全地提取文件名（去掉扩展名）
      const lastDotIndex = originalFilename.lastIndexOf('.');
      let baseFilename;
      if (lastDotIndex > 0) {
        baseFilename = originalFilename.substring(0, lastDotIndex);
      } else {
        // 如果没有扩展名，使用完整文件名
        baseFilename = originalFilename;
      }

      // 统一小写进行匹配，增加匹配的健壮性
      const targetFilename = baseFilename.toLowerCase().trim();
      const matchedData = dataRows.find(data =>
        data.filename.toLowerCase().trim() === targetFilename
      );

      if (matchedData) {
        matchedFiles.push({
          file: fileObj,
          data: matchedData
        });
      } else {
        unmatchedFiles.push(originalFilename);
      }
    });

    return {
      matchedFiles,
      unmatchedFiles,
      isMatched: matchedFiles.length > 0
    };
  } catch (error) {
    throw error;
  }
};

/**
 * 获取默认的JSON/Excel数据格式说明
 * @param type - 数据类型，如 'photo', 'status' 等
 * @returns 格式说明文本或图片路径
 */
export const getJsonFormatDescription = (type?: string): string => {
  if (type === 'photo') {
    // 返回图片路径，使用服务器对应的静态路径
    return '/assets/TemplateImg/photoMatch.png';
  }
  if (type === 'status') {
    // 返回状态格式说明，使用服务器对应的静态路径
    return '/assets/TemplateImg/statusMatch.png';
  }
  // 默认返回文本格式说明
  return `照片文件名\t照片标题\t关联机器\t标签\t备注
5328\t测试标题1\tVP-BF-210-10\t标签1,标签2\t测试备注1
1024\t测试标题2\tVP-BF-210-10\t标签4,标签3\t测试备注2`;
};