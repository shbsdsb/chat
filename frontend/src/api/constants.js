import { useAlertStore } from "@/stores/alert";

export const HTTP_STATUS_MSG = {
  400: "请求参数有误，请检查输入内容",
  401: "认证失败，请检查 API Key 是否正确",
  402: "账户余额不足，请充值后重试",
  403: "没有访问权限，请检查 API Key 权限",
  404: "请求的资源不存在",
  405: "请求方法不被允许",
  408: "请求超时，请检查网络后重试",
  409: "资源冲突，请刷新后重试",
  410: "请求的资源已被永久删除",
  413: "请求体过大",
  415: "不支持的媒体类型",
  422: "请求参数验证失败",
  429: "请求过于频繁，请稍后重试",
  500: "服务器内部错误，请稍后重试",
  502: "网关错误，服务可能正在重启",
  503: "服务暂时不可用，请稍后重试",
  504: "网关超时，请稍后重试",
};

export function getHttpStatusMessage(status) {
  const msg = HTTP_STATUS_MSG[status];
  return msg ? `${msg}（${status}）` : `请求失败（HTTP ${status}）`;
}

let _alertFn = null;
export function getAlert() {
  if (!_alertFn) {
    try {
      _alertFn = useAlertStore();
    } catch {
      _alertFn = null;
    }
  }
  return _alertFn;
}
