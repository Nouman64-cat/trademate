/**
 * AudioWorklet processor — buffers mic input to 4096-sample chunks
 * then posts Float32Array to the main thread for WebSocket transmission.
 * Replaces the deprecated ScriptProcessorNode.
 */
class MicProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._buffer = new Float32Array(4096);
    this._offset = 0;
  }

  process(inputs) {
    const channel = inputs[0]?.[0];
    if (!channel) return true;

    let src = 0;
    while (src < channel.length) {
      const room = this._buffer.length - this._offset;
      const n = Math.min(room, channel.length - src);
      this._buffer.set(channel.subarray(src, src + n), this._offset);
      this._offset += n;
      src += n;

      if (this._offset >= this._buffer.length) {
        this.port.postMessage(this._buffer.slice());
        this._offset = 0;
      }
    }
    return true; // keep processor alive
  }
}

registerProcessor("mic-processor", MicProcessor);
