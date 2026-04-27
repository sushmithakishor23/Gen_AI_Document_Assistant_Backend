# 🚀 Quick Start - MVP Demo

## Start in 3 Steps

### 1️⃣ Activate Environment & Set API Key
```powershell
.\venv\Scripts\Activate.ps1
$env:OPENAI_API_KEY='your-actual-key-here'
```

### 2️⃣ Install New Dependency (if needed)
```powershell
pip install aiofiles
```

### 3️⃣ Launch the Chat UI
```powershell
# Easiest way - auto-opens browser
python start_chat_ui.py

# Or manually
python main.py
# Then open: http://localhost:8000
```

---

## 🎯 Demo Flow (2 minutes)

### Upload Phase
1. **Open** http://localhost:8000
2. **Click** "Choose a file"
3. **Select** `data/test_files/sample_ml.txt`
4. **Click** "Upload"
5. **Wait** for "✓ Successfully ingested..." message

### Chat Phase
6. **Type** a question: "What is machine learning?"
7. **Press** Enter or click "Send"
8. **Watch** loading animation (bouncing dots)
9. **See** AI response appear in chat
10. **Click** "Sources" to expand citations
11. **View** filename, page numbers, and snippets

### Test More
- Ask follow-up: "What are the applications?"
- Try another file: `sample_document.pdf`
- Test error: Query before uploading → See error message

---

## 📁 Sample Files Ready to Use

Located in `data/test_files/`:
- ✅ `sample_ml.txt` - Machine learning content
- ✅ `sample_document.pdf` - PDF document
- ✅ `small.txt` - Small text file
- ⚠️ `image.jpg` - Will be rejected (images not supported)

---

## 🎨 What You'll See

### Header (Purple Gradient)
```
🤖 Gen AI Document Assistant
Upload documents and ask questions - powered by AI
```

### Upload Section (Light Gray)
```
[Choose a file (PDF, DOCX, TXT)] [Upload]
```

### Chat Area (White Background)
```
User (You):   "What is machine learning?"  →
              (Purple bubble, right side)

↓ Loading dots animation ↓

← AI: "Machine learning is a branch of..."
   (Gray bubble, left side)
   
   [▼ Sources (3)]  ← Click to expand
```

### Expanded Sources
```
📄 sample_ml.txt  Page 1  Match: 92.3%
"Machine learning is a method of data analysis..."

📄 sample_ml.txt  Page 1  Match: 87.5%
"The main applications include..."
```

---

## ⚡ Features Checklist

✅ **Upload**: PDF, DOCX, TXT files  
✅ **Chat**: Real-time Q&A with AI  
✅ **Sources**: Collapsible citations with metadata  
✅ **Loading**: Animated spinner while processing  
✅ **Errors**: User-friendly error messages  
✅ **UX**: Auto-scroll, auto-resize input, smooth animations  

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't open http://localhost:8000 | Server not running - check terminal |
| "No documents found" error | Upload a document first |
| Upload fails | Check file type (PDF/DOCX/TXT only) |
| Network error | Server stopped - restart with `python main.py` |
| CORS error | Already configured - try refreshing page |
| API key error | Set: `$env:OPENAI_API_KEY='key'` |

---

## 📸 Screenshot Reference

### Initial State
- Empty chat area with message: "No messages yet"
- Upload section at top
- Input box at bottom

### After Upload
- Green success message appears
- Shows chunk count

### During Query
- User message on right (purple)
- Loading dots on left (gray)

### After Response
- AI message on left (gray)
- Sources button below answer
- Chat scrolls to bottom automatically

---

## 🎉 End of Day Goal: ACHIEVED!

**MVP Status: COMPLETE** ✅

- ✅ Frontend chat UI
- ✅ Connected to POST /query endpoint
- ✅ Display answers in chat bubbles
- ✅ Source citations (filename + page + snippet)
- ✅ Loading states
- ✅ Error handling

**Ready to demo!** 🚀

---

## 💡 Demo Tips

1. **Keep terminal visible** - Shows API logs
2. **Test happy path first** - Upload → Query → Success
3. **Show sources** - Click to expand citations
4. **Demonstrate errors** - Query before upload
5. **Multiple questions** - Show conversation flow
6. **Different files** - Upload PDF and TXT

---

## 🔄 Quick Reset (if needed)

```powershell
# Stop server: Ctrl+C
# Clear vector DB (fresh start)
Remove-Item -Recurse -Force chroma_db
# Restart
python start_chat_ui.py
```

---

**Time to demo:** ~2 minutes  
**Wow factor:** High! 🌟
