// src/utils/date.ts
export function getCurrentDateTime(format: 'datetime' | 'date' | 'time' = 'datetime'): string {
  const now = new Date()

  const pad = (n: number) => n.toString().padStart(2, '0')

  const year = now.getFullYear()
  const month = pad(now.getMonth() + 1)
  const day = pad(now.getDate())

  const hours = pad(now.getHours())
  const minutes = pad(now.getMinutes())
  const seconds = pad(now.getSeconds())

  switch (format) {
    case 'date':
      return `${year}-${month}-${day}`
    case 'time':
      return `${hours}:${minutes}:${seconds}`
    case 'datetime':
    default:
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  }
}

export function getTodayDateObject(): Date {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), now.getDate())
}

export function timeToIsoString(timeStr: string): string {
  if (!timeStr) {
    console.error(`Invalid time value: ${timeStr}`); // 빈 값 처리
    return ''; // 빈 값 반환
  }

  // timeStr이 'HH:mm' 형식일 경우 처리
  if (/^\d{2}:\d{2}$/.test(timeStr)) {
    const [hour, minute] = timeStr.split(':').map(Number);
    const base = new Date();
    base.setHours(hour, minute, 0, 0); // 시간, 분 설정
    return base.toISOString(); // ISO 형식 반환
  }

  // timeStr이 ISO 형식인 경우 처리
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/.test(timeStr)) {
    return timeStr;  // 이미 ISO 형식이므로 그대로 반환
  }

  console.error(`Invalid time format: ${timeStr}`);  // 잘못된 형식 처리
  return ''; // 잘못된 형식일 경우 빈 값 반환
}

export function convertTimeStrToMinutes(timeStr: string): number {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours * 60 + minutes;
}

