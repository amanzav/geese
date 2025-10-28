import { NextRequest, NextResponse } from 'next/server'

// API endpoint to trigger Python automation scripts
export async function POST(request: NextRequest) {
  try {
    const { action, folderName } = await request.json()
    
    if (!folderName) {
      return NextResponse.json({ error: 'Folder name is required' }, { status: 400 })
    }
    
    // Return instructions for now since we need to set up Python backend API
    const instructions = {
      action,
      folderName,
      message: 'To enable automation, you need to run the Python backend server',
      command: generateCommand(action, folderName)
    }
    
    return NextResponse.json(instructions)
  } catch (error) {
    console.error('Error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

function generateCommand(action: string, folderName: string): string {
  switch (action) {
    case 'generate_cover_letters':
      return `python main.py generate-cover-letters --folder "${folderName}"`
    case 'apply_all':
      return `python main.py apply --folder "${folderName}"`
    case 'upload_cover_letters':
      return `python main.py upload-cover-letters --folder "${folderName}"`
    default:
      return ''
  }
}
