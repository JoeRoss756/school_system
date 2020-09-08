# Course Managment System
## Building and Running
In order to run the application, move into the top directory where the `docker-compose.yml`
is located, and run the command: `docker-compose up`. 
This will build the image used for the server using the existing dockerfile, and start the required
containers to run the application, mongodb and redis.

The `config.yml` file controls that parameters that are used to connect to Mongo and Redis, as well
as the port the application server runs on. The server is configured by default to run on port 8889.
Mongodb runs on port 27017 (default) and Redis runs on port 6379 (default.)

## API endpoints
The server supports creating, updating, getting and deleting students, grades and courses. Deleting or
modifying an object will cause related objects to be modified or deleted as well.  

Caching is supported for that statistics endpoints, that is to say that so long as the underlying data
remains unchanged, results will be returned from a cache. Updating or deleting course or grades will
cause the cache to be invalidated. 
### Student
#### GET  
*url:* http://0.0.0.0:8889/students?id_number={student_id}  
#### POST  
*url:* http://0.0.0.0:8889/students    
*body:* `{id_number: int, first_name: str, last_name: str, email: str}`  
#### PUT  
*url:* http://0.0.0.0:8889/students  
*body:* `{current_id: int, new: {id_number: int, first_name: str, last_name: str, email: str}}`  
#### DELETE  
*url:* http://0.0.0.0:8889/students  
*body:* `{id_number: int}`  

### Course  
#### GET  
*url:* http://0.0.0.0:8889/courses?course_id={course_id}  
#### POST  
*url:* http://0.0.0.0:8889/courses    
*body:* `{course_id: int, name: str, students: list<int>}`  
#### PUT  
*url:* http://0.0.0.0:8889/courses  
*body:* `{current_id: int, new: {course_id: int, name: str, students: list<int>}}`  
#### DELETE  
*url:* http://0.0.0.0:8889/courses  
*body:* `{course_id: int}`  

### Grade
#### GET  
*url:* http://0.0.0.0:8889/grades?student_id={student_id}&course_id=={course_id}  
#### POST  
*url:* http://0.0.0.0:8889/grades    
*body:* `{course_id: int, student_id: str, grade: <numeric>}`  
#### PUT  
*url:* http://0.0.0.0:8889/grades  
*body:* `{current_sid: int, current_cid: int, new: {course_id: int, student_id: int, grade: numeric}}`  
#### DELETE  
*url:* http://0.0.0.0:8889/grades  
*body:* `{course_id: int, student_id: int}`  


### Statistics
#### Student with the highest average  
*url:* http://0.0.0.0:8889/best_student

#### Course with the highest average  
*url:* http://0.0.0.0:8889/easiest_course
