/** Render text (usually a URL) as a PNG data URL for QR display. */
export async function toQrDataUrl(text: string, size = 220): Promise<string> {
  const QRCode = await import('qrcode')
  return QRCode.toDataURL(text, {
    width: size,
    margin: 2,
    color: { dark: '#1a3d2e', light: '#ffffff' }
  })
}
