import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './style.css'

export default function App() {
  const [state, setState] = useState('idle')
  const [fullText, setFullText] = useState('您好，我是語音機器人，有什麼可以幫助您的嗎？')  // 真正的文字
  const [displayText, setDisplayText] = useState('')  // 打字動畫正在顯示的文字
  const typingInterval = 200 // 打字速度(ms)

  const eyeL = useRef()
  const eyeR = useRef()
  const browL = useRef()
  const browR = useRef()
  const frownL = useRef()
  const frownR = useRef()
  const sweat = useRef()
  const mouth = useRef()
  const questions = useRef([])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === '1') setState('idle')
      if (e.key === '2') setState('thinking')
      if (e.key === '3') setState('talking')
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  useEffect(() => {
    let blinkInterval

    ;[browL, browR, frownL, frownR].forEach(el => el.current.style.display = 'none')
    questions.current.forEach(el => el.style.display = 'none')
    eyeL.current.classList.remove('blink')
    eyeR.current.classList.remove('blink')
    eyeL.current.style.display = 'block'
    eyeR.current.style.display = 'block'
    sweat.current.classList.remove('animate')
    mouth.current.className = 'mouth'

    if (state === 'idle') {
      mouth.current.classList.add('idle')
    }
    if (state === 'thinking') {
      browL.current.style.display = 'block'
      browR.current.style.display = 'block'
      browL.current.className = 'eyebrow thinking-horizontal left'
      browR.current.className = 'eyebrow thinking-horizontal right'
      eyeL.current.style.display = 'none'
      eyeR.current.style.display = 'none'
      frownL.current.style.display = 'block'
      frownR.current.style.display = 'block'
      mouth.current.classList.add('thinking')
      questions.current.forEach(el => el.style.display = 'block')
    }
    if (state === 'talking') {
      mouth.current.classList.add('talking')
      blinkInterval = setInterval(() => {
        eyeL.current.classList.add('blink')
        eyeR.current.classList.add('blink')
        setTimeout(() => {
          eyeL.current.classList.remove('blink')
          eyeR.current.classList.remove('blink')
        }, 200)
      }, 2000)
    }

    return () => clearInterval(blinkInterval)
  }, [state])

  // 打字動畫
  useEffect(() => {
    let idx = 0
    setDisplayText('')
    if (!fullText) return

    const interval = setInterval(() => {
      setDisplayText(prev => {
        const nextText = prev + fullText.charAt(idx)
        idx++
        if (idx >= fullText.length) clearInterval(interval)
        return nextText
      })
    }, typingInterval)

    return () => clearInterval(interval)
  }, [fullText])

  // const handleVoiceInteraction = async () => {
  //   setFullText("🎙️ 聆聽中...")
  //   setState('thinking')
  
  //   const audio = new Audio()  // ✅ 一開始就建好 audio，這樣瀏覽器允許播放
  
  //   try {
  //     const res = await axios.post("http://localhost:5001/process_audio")
  //     const text = res.data.reply
  //     const audioUrl = res.data.audio_url
  
  //     audio.src = audioUrl
  //     audio.load()  // 重新載入新的 audio 檔案
  
  //     const playPromise = audio.play()  // 嘗試播放
  //     if (playPromise !== undefined) {
  //       playPromise.then(() => {
  //         setFullText('')  // 清空畫面
  //         setState('talking')  // 切成 talking
  //         setTimeout(() => {
  //           setFullText(text)  // 延遲開始打字
  //         }, 300)
  //       }).catch(error => {
  //         console.error("播放失敗：", error)
  //         setFullText(text)  // 播放失敗也至少打字
  //         setState('talking')
  //       })
  //     }
  
  //   } catch (err) {
  //     console.error(err)
  //     setFullText("❌ 發生錯誤，請稍後再試")
  //     setState('idle')
  //   }
  // }
  
  const handleVoiceInteraction = async () => {
    setFullText("🎙️ 聆聽中...")
    setState('thinking')
  
    try {
      const res = await axios.post("http://localhost:5001/process_audio")
      setFullText(res.data.reply)
      setState('talking')
  
      // ✅ 開始輪詢詢問後端是否播放完
      const intervalId = setInterval(async () => {
        const status = await axios.get("http://localhost:5001/audio_status")
        if (!status.data.playing) {
          clearInterval(intervalId)
          setState('idle')
        }
      }, 1000) // 每 1秒問一次
  
    } catch (err) {
      console.error(err)
      setFullText("❌ 發生錯誤，請稍後再試")
      setState('idle')
    }
  }
  
  
  
  
  

  return (
    <div className="main-container">
      <h1>語音機器人</h1>
      <div className="content">
        <div className="left-panel">
          <div className="face" id="face">
            <div className="eyebrow left" ref={browL}></div>
            <div className="eyebrow right" ref={browR}></div>
            <div className="eye left" ref={eyeL}></div>
            <div className="eye right" ref={eyeR}></div>
            <div className="frown left" ref={frownL}></div>
            <div className="frown right" ref={frownR}></div>
            <div className="sweat" ref={sweat}></div>
            <div className="mouth" ref={mouth}></div>
            {['q1', 'q2', 'q3'].map((q, i) => (
              <div key={q} className={`question ${q}`} ref={el => questions.current[i] = el}>?</div>
            ))}
          </div>
          <button className="record-btn" onClick={handleVoiceInteraction}>🎤 語音互動</button>
        </div>

        <div className="dialogue-box">
          <p>{displayText}</p> {/* 用 displayText 打字顯示 */}
        </div>
      </div>
    </div>
  )
}
