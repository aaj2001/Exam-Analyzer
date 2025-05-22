#!/usr/bin/env python3
"""
Batch Processor for Automated Exam Grading and Cheating Detection
Based on the same algorithms as the web and GUI applications
"""

import argparse
import os
import csv
import sys
import json
from similarity import (
    calculate_levenshtein_similarity, 
    calculate_jaccard_similarity, 
    analyze_essays_levenshtein, 
    analyze_mcq_jaccard, 
    detect_cheating_essays, 
    detect_cheating_mcq
)

def parse_mcq_file(file_path):
    """Parse MCQ file (CSV or TXT) and return a dictionary of answers"""
    answers = {}
    
    with open(file_path, 'r') as f:
        content = f.read()
        
        # Determine file type and parse accordingly
        if file_path.endswith('.csv'):
            import io
            import csv
            csv_reader = csv.reader(io.StringIO(content))
            for row in csv_reader:
                if len(row) >= 2:
                    question_num = row[0].strip()
                    answer = row[1].strip()
                    answers[question_num] = answer
        else:  # Assume it's a text file
            lines = content.strip().split('\n')
            for line in lines:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    question_num = parts[0].strip()
                    answer = parts[1].strip()
                    answers[question_num] = answer
    
    return answers

def process_mcq(reference_file, student_files, output_file=None):
    """Process MCQ files and generate results"""
    print(f"Processing MCQ analysis with reference file: {reference_file}")
    print(f"Student files: {', '.join(student_files)}")
    
    try:
        # Parse reference file
        reference_answers = parse_mcq_file(reference_file)
        
        if not reference_answers:
            print("Error: No reference answers found in the reference file.")
            return
        
        print(f"Found {len(reference_answers)} questions in reference file.")
        
        # Parse student files
        student_answers = {}
        for file_path in student_files:
            try:
                student_name = os.path.basename(file_path).rsplit('.', 1)[0]
                answers = parse_mcq_file(file_path)
                student_answers[student_name] = answers
                print(f"Processed student file: {student_name}")
            except Exception as e:
                print(f"Error processing student file {file_path}: {str(e)}")
        
        if not student_answers:
            print("Error: No valid student files were processed.")
            return
        
        # Analyze student answers
        print("Analyzing MCQ answers...")
        results = analyze_mcq_jaccard(reference_answers, student_answers)
        
        # Display results
        print("\nMCQ Analysis Results:")
        print("=====================")
        print(f"{'Student':<30} {'Score':<10} {'Similarity':<10}")
        print("-" * 50)
        
        for student, data in results.items():
            print(f"{student:<30} {data['score']}/{data['total']:<10} {data['similarity']:.2f}")
        
        # Export results to CSV if requested
        if output_file:
            export_mcq_results(results, output_file)
            print(f"Results exported to {output_file}")
        
        return results
    
    except Exception as e:
        print(f"Error during MCQ analysis: {str(e)}")
        return None

def process_essays(reference_file, student_files, threshold=0.8, output_file=None):
    """Process essay files and generate results"""
    print(f"Processing essay analysis with reference file: {reference_file}")
    print(f"Student files: {', '.join(student_files)}")
    print(f"Similarity threshold for cheating detection: {threshold}")
    
    try:
        # Read reference essay
        with open(reference_file, 'r') as f:
            reference_essay = f.read()
        
        if not reference_essay:
            print("Error: Reference essay is empty.")
            return
        
        # Read student essays
        student_essays = {}
        for file_path in student_files:
            try:
                student_name = os.path.basename(file_path).rsplit('.', 1)[0]
                with open(file_path, 'r') as f:
                    student_essays[student_name] = f.read()
                print(f"Processed student file: {student_name}")
            except Exception as e:
                print(f"Error processing student file {file_path}: {str(e)}")
        
        if not student_essays:
            print("Error: No valid student files were processed.")
            return
        
        # Analyze essays
        print("Analyzing essays...")
        results = analyze_essays_levenshtein(reference_essay, student_essays)
        
        # Detect potential cheating
        print(f"Detecting potential academic dishonesty (threshold: {threshold})...")
        cheating_report = detect_cheating_essays(student_essays, threshold)
        
        # Display results
        print("\nEssay Analysis Results:")
        print("======================")
        print(f"{'Student':<30} {'Similarity':<10}")
        print("-" * 50)
        
        for student, similarity in results.items():
            print(f"{student:<30} {similarity:.2f}")
        
        # Display cheating report
        print("\nPotential Academic Dishonesty Report:")
        print("====================================")
        
        if not cheating_report:
            print("No potential academic dishonesty detected.")
        else:
            print(f"{'Student A':<30} {'Student B':<30} {'Similarity':<10}")
            print("-" * 70)
            
            for pair, similarity in cheating_report.items():
                student_a, student_b = pair.split(' - ')
                print(f"{student_a:<30} {student_b:<30} {similarity:.2f}")
        
        # Export results to CSV if requested
        if output_file:
            export_essay_results(results, cheating_report, output_file)
            print(f"Results exported to {output_file}")
        
        return results, cheating_report
    
    except Exception as e:
        print(f"Error during essay analysis: {str(e)}")
        return None

def export_mcq_results(results, output_file):
    """Export MCQ results to CSV file"""
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['Student', 'Score', 'Similarity Score'])
        
        # Write data rows
        for student, data in results.items():
            writer.writerow([student, f"{data['score']}/{data['total']}", f"{data['similarity']:.2f}"])

def export_essay_results(results, cheating_report, output_file):
    """Export essay results to CSV file"""
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['Student', 'Similarity Score'])
        
        # Write data rows
        for student, similarity in results.items():
            writer.writerow([student, f"{similarity:.2f}"])
        
        # Add a blank row
        writer.writerow([])
        
        # Write cheating section
        writer.writerow(['Potential Academic Dishonesty Detected'])
        writer.writerow(['Student A', 'Student B', 'Similarity'])
        
        for pair, similarity in cheating_report.items():
            student_a, student_b = pair.split(' - ')
            writer.writerow([student_a, student_b, f"{similarity:.2f}"])

def main():
    """Main entry point for the batch processor"""
    parser = argparse.ArgumentParser(description='Batch Processor for Automated Exam Grading')
    parser.add_argument('--type', choices=['mcq', 'essay'], required=True, help='Type of analysis to perform')
    parser.add_argument('--reference', required=True, help='Path to reference file')
    parser.add_argument('--students', nargs='+', required=True, help='Paths to student files')
    parser.add_argument('--threshold', type=float, default=0.8, help='Similarity threshold for cheating detection (essay only)')
    parser.add_argument('--output', help='Path to output CSV file')
    
    args = parser.parse_args()
    
    if args.type == 'mcq':
        process_mcq(args.reference, args.students, args.output)
    else:
        process_essays(args.reference, args.students, args.threshold, args.output)

if __name__ == "__main__":
    main()