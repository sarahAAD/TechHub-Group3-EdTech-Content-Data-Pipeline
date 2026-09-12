================================================================================
TASK 3 - INPUT SCHEMA DEFINITION DATA CONTRACT
================================================================================
Column Name        | Data Type    | Nullable | Allowed Values / Constraints
--------------------------------------------------------------------------------
source             | String       | No       | Must be exactly 'Pluralsight'
category           | String       | No       | Must be 'AI & Data' or 'Cloud'
title              | String       | No       | Non-empty character string
author             | String       | Yes      | Text string tracking writer bylines
publication_date   | String (ISO) | Yes      | Must match YYYY-MM-DD standard format
description        | String       | Yes      | Summary text blocks
tags               | String       | Yes      | Comma-separated tracking keywords
url                | String       | No       | Must start with 'https://'
content            | String       | No       | Full extracted article text content
scraped_at         | String (ISO) | No       | Valid ISO execution timestamp
--------------------------------------------------------------------------------
