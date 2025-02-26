const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Set up EJS as the templating engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Set up middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public')));

// Routes
app.get('/', (req, res) => {
  // Get the job listings from the most recent file
  const outputDir = path.join(__dirname, 'output');
  let jobListings = [];
  let latestFile = null;
  let allFiles = [];
  
  try {
    if (fs.existsSync(outputDir)) {
      // Get a list of all job listing files
      allFiles = fs.readdirSync(outputDir)
        .filter(file => file.startsWith('all_jobs_') && file.endsWith('.json'))
        .sort()
        .reverse(); // Most recent first
      
      if (allFiles.length > 0) {
        latestFile = allFiles[0];
        const filePath = path.join(outputDir, latestFile);
        const fileContent = fs.readFileSync(filePath, 'utf8');
        jobListings = JSON.parse(fileContent);
      }
    }
  } catch (error) {
    console.error('Error reading job listings:', error);
  }
  
  // Render the index page with data
  res.render('index', {
    title: 'LinkedIn Job Scraper',
    jobs: jobListings,
    latestFile: latestFile,
    allFiles: allFiles,
    jobCount: jobListings.length
  });
});

// Route to execute the scraper
app.post('/run-scraper', (req, res) => {
  const { title, location, experience } = req.body;
  
  if (!title || !location) {
    return res.status(400).json({ 
      success: false, 
      error: 'Job title and location are required' 
    });
  }
  
  console.log(`Running scraper for: ${title} in ${location} with ${experience} years experience`);
  
  // Build the command to execute the Python script
  const cmd = `python job_scraper.py --title "${title}" --location "${location}" --experience "${experience}"`;
  
  // Set a timeout for the scraper process (15 minutes)
  const timeout = 15 * 60 * 1000;
  
  // For AJAX requests, we'll respond with JSON
  const isAjaxRequest = req.xhr || req.headers.accept.indexOf('json') > -1;
  
  // Execute the command with a timeout
  const scraperProcess = exec(cmd, { timeout: timeout }, (error, stdout, stderr) => {
    if (error) {
      console.error(`Error executing scraper: ${error.message}`);
      
      // Different response based on request type
      if (isAjaxRequest) {
        return res.status(500).json({ 
          success: false, 
          error: 'Failed to run the scraper', 
          details: error.message,
          output: stdout || null
        });
      } else {
        // For traditional form submission, redirect with error parameter
        return res.redirect('/?error=' + encodeURIComponent('Failed to run the scraper: ' + error.message));
      }
    }
    
    if (stderr) {
      console.error(`Scraper stderr: ${stderr}`);
    }
    
    console.log(`Scraper output: ${stdout}`);
    
    // Try to determine the output file from the stdout
    let outputFile = null;
    const fileMatch = stdout.match(/Results (?:will be |)saved to: .*?output[\/\\](.*?\.json)/i);
    if (fileMatch && fileMatch[1]) {
      outputFile = fileMatch[1];
    }
    
    // Different response based on request type
    if (isAjaxRequest) {
      return res.status(200).json({ 
        success: true, 
        message: 'Scraper completed successfully',
        output: stdout,
        outputFile: outputFile
      });
    } else {
      // For traditional form submission
      if (outputFile) {
        return res.redirect('/?file=' + encodeURIComponent(outputFile));
      } else {
        return res.redirect('/');
      }
    }
  });
  
  // Respond immediately for AJAX requests to prevent timeout
  if (isAjaxRequest) {
    res.status(202).json({ 
      success: true, 
      message: 'Scraper started successfully',
      estimatedTime: 'Several minutes'
    });
  }
  // For traditional form submissions, the response will come from the exec callback
});

// API endpoint to get job listings
app.get('/api/jobs', (req, res) => {
  const outputDir = path.join(__dirname, 'output');
  let jobListings = [];
  
  try {
    if (fs.existsSync(outputDir)) {
      const files = fs.readdirSync(outputDir)
        .filter(file => file.startsWith('all_jobs_') && file.endsWith('.json'))
        .sort()
        .reverse();
      
      if (files.length > 0) {
        const filePath = path.join(outputDir, files[0]);
        const fileContent = fs.readFileSync(filePath, 'utf8');
        jobListings = JSON.parse(fileContent);
      }
    }
  } catch (error) {
    console.error('Error reading job listings:', error);
    return res.status(500).json({ error: 'Failed to load job listings' });
  }
  
  res.json(jobListings);
});

// Add a new route to get job data for a specific file
app.get('/jobs/:filename', (req, res) => {
  const filename = req.params.filename;
  const filePath = path.join(__dirname, 'output', filename);
  
  try {
    if (fs.existsSync(filePath)) {
      const fileContent = fs.readFileSync(filePath, 'utf8');
      const jobListings = JSON.parse(fileContent);
      res.json({
        success: true,
        jobs: jobListings,
        jobCount: jobListings.length,
        filename: filename
      });
    } else {
      res.status(404).json({ success: false, error: 'File not found' });
    }
  } catch (error) {
    console.error(`Error reading job file ${filename}:`, error);
    res.status(500).json({ success: false, error: 'Failed to read job file' });
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
}); 